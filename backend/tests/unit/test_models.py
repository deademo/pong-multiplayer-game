"""
Unit tests for Django models.
"""
import pytest
from django.utils import timezone
from pong.models import MatchHistory


@pytest.mark.django_db
class TestMatchHistory:
    """Test MatchHistory model."""
    
    def test_match_creation(self):
        """Save a match and verify it's created."""
        match = MatchHistory.objects.create(
            room_code="TEST001",
            player1_score=5,
            player2_score=3,
            winner="Player 1",
            points_limit=5
        )
        
        assert match.id is not None
        assert match.room_code == "TEST001"
    
    def test_match_retrieval(self):
        """Read a match from database."""
        MatchHistory.objects.create(
            room_code="TEST002",
            player1_score=10,
            player2_score=20,
            winner="Player 2",
            points_limit=20
        )
        
        match = MatchHistory.objects.get(room_code="TEST002")
        
        assert match.player1_score == 10
        assert match.player2_score == 20
        assert match.winner == "Player 2"
        assert match.points_limit == 20
    
    def test_score_values(self):
        """Ensure scores are stored correctly."""
        match = MatchHistory.objects.create(
            room_code="TEST003",
            player1_score=0,
            player2_score=5,
            winner="Player 2",
            points_limit=5
        )
        
        assert match.player1_score == 0
        assert match.player2_score == 5
    
    def test_timestamp_auto_add(self):
        """created_at is automatically set."""
        match = MatchHistory.objects.create(
            room_code="TEST004",
            player1_score=5,
            player2_score=2,
            winner="Player 1",
            points_limit=5
        )
        
        assert match.created_at is not None
        assert isinstance(match.created_at, type(timezone.now()))
    
    def test_multiple_matches_same_room(self):
        """Multiple matches can have the same room code (rematches)."""
        MatchHistory.objects.create(
            room_code="RETEST",
            player1_score=5,
            player2_score=3,
            winner="Player 1",
            points_limit=5
        )
        
        MatchHistory.objects.create(
            room_code="RETEST",
            player1_score=3,
            player2_score=5,
            winner="Player 2",
            points_limit=5
        )
        
        matches = MatchHistory.objects.filter(room_code="RETEST")
        assert matches.count() == 2
    
    def test_string_representation(self):
        """Test __str__ method."""
        match = MatchHistory.objects.create(
            room_code="TEST005",
            player1_score=5,
            player2_score=3,
            winner="Player 1",
            points_limit=5
        )
        
        string_repr = str(match)
        assert "TEST005" in string_repr
        assert "Player 1" in string_repr
        assert "5" in string_repr
        assert "3" in string_repr
