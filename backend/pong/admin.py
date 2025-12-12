from django.contrib import admin
from .models import MatchHistory


@admin.register(MatchHistory)
class MatchHistoryAdmin(admin.ModelAdmin):
    list_display = ['room_code', 'winner', 'player1_score', 'player2_score', 'points_limit', 'created_at']
    list_filter = ['winner', 'points_limit', 'created_at']
    search_fields = ['room_code']
    readonly_fields = ['created_at']
