from django.contrib import admin
from .models import User, Profile, SubscriptionPlan, UserSubscription, OfflineDevice

admin.site.register(User)
admin.site.register(Profile)
admin.site.register(SubscriptionPlan)
admin.site.register(UserSubscription)
admin.site.register(OfflineDevice)
