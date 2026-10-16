from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.statistics.models import SubjectStats
from .models import PointEvent
from .services import display_name

TOP_N = 50


def _period_start(period):
    today = timezone.localdate()
    if period == "week":
        return today - timedelta(days=today.weekday())
    if period == "month":
        return today.replace(day=1)
    return None


class LeaderboardView(APIView):
    """GET /leaderboard/?period=week|month|all

    Javob: {period, entries: [1..50 o'rin], me: {rank, points} | null, participants}
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        period = request.query_params.get("period", "week")
        if period not in ("week", "month", "all"):
            period = "week"
        start = _period_start(period)

        if start is None:
            rows = (
                SubjectStats.objects.values("user_id").annotate(points=Sum("total_points"))
                .filter(points__gt=0).order_by("-points", "user_id")
            )
        else:
            rows = (
                PointEvent.objects.filter(created_at__date__gte=start)
                .values("user_id").annotate(points=Sum("points"))
                .filter(points__gt=0).order_by("-points", "user_id")
            )
        rows = list(rows)

        # Bir xil ballga bir xil o'rin (1, 2, 2, 4 ...)
        ranked, prev_points, prev_rank = [], None, 0
        for i, r in enumerate(rows, start=1):
            rank = prev_rank if r["points"] == prev_points else i
            ranked.append({**r, "rank": rank})
            prev_points, prev_rank = r["points"], rank

        top = ranked[:TOP_N]
        User = get_user_model()
        users = {u.id: u for u in User.objects.filter(id__in=[r["user_id"] for r in top])}
        streaks = {
            s["user_id"]: s["streak"]
            for s in SubjectStats.objects.filter(user_id__in=users.keys()).values("user_id")
            .annotate(streak=Sum("current_streak_days"))
        }
        from apps.subjects.models import UserSubjectLevel
        levels = {}
        for row in UserSubjectLevel.objects.filter(user_id__in=users.keys(), subject__code="english",
                                                   current_level__isnull=False).select_related("current_level"):
            levels[row.user_id] = row.current_level.code

        entries = []
        for r in top:
            u = users.get(r["user_id"])
            if not u:
                continue
            entries.append({
                "rank": r["rank"],
                "name": display_name(u),
                "username": u.username,  # eski frontend (admin) uchun
                "points": r["points"],
                "total_points": r["points"],
                "level": levels.get(u.id),
                "streak": streaks.get(u.id, 0),
                "is_me": u.id == request.user.id,
            })

        me = next((r for r in ranked if r["user_id"] == request.user.id), None)
        return Response({
            "period": period,
            "since": start.isoformat() if start else None,
            "entries": entries,
            "me": {"rank": me["rank"], "points": me["points"], "name": display_name(request.user)} if me else None,
            "participants": len(ranked),
        })
