from django.db import models
from django.utils import timezone


class MatchHistory(models.Model):
    """Store completed match results."""
    room_code = models.CharField(max_length=50, db_index=True)
    player1_score = models.IntegerField()
    player2_score = models.IntegerField()
    winner = models.CharField(max_length=20)  # "Player 1" or "Player 2"
    points_limit = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Match Histories'

    def __str__(self):
        return f"{self.room_code}: {self.winner} ({self.player1_score}-{self.player2_score})"
