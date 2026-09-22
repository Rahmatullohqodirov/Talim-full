from django.db.models import Sum
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import LeaderboardEntry
from .serializers import LeaderboardEntrySerializer


class LeaderboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        scope = request.query_params.get("scope", "global_anon")
        week_start = timezone.now().date() - timezone.timedelta(days=timezone.now().weekday())

        # Foydalanuvchi uchun joriy hafta yozuvini avtomatik yaratamiz.
        from apps.statistics.models import SubjectStats
        points = SubjectStats.objects.filter(user=request.user).aggregate(
            total=Sum("total_points")
        )["total"] or 0
        LeaderboardEntry.objects.update_or_create(
            user=request.user, scope=scope, week_start=week_start,
            defaults={"total_points": int(points)},
        )

        # Rank har safar ball bo'yicha qayta hisoblanadi.
        entries = list(
            LeaderboardEntry.objects.filter(scope=scope, week_start=week_start)
            .select_related("user")
            .order_by("-total_points", "user__username")[:50]
        )
        for rank, entry in enumerate(entries, start=1):
            if entry.rank != rank:
                LeaderboardEntry.objects.filter(pk=entry.pk).update(rank=rank)
                entry.rank = rank

        return Response(LeaderboardEntrySerializer(entries, many=True).data)
