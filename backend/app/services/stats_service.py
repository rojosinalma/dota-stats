from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from ..models import Match, Hero, PlayerEncountered
from ..schemas.stats import HeroStats, PlayerStats, TimeStats, PlayerEncounteredStats, DashboardStats


class StatsService:
    def __init__(self, db: Session):
        self.db = db

    def get_player_stats(
        self,
        user_id: int,
        hero_id: Optional[int] = None,
        game_mode: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> PlayerStats:
        """Get overall player statistics"""
        # Only query matches with details (not stubs)
        query = self.db.query(Match).filter(
            Match.user_id == user_id,
            Match.has_details == True
        )

        # Apply filters
        query = self._apply_filters(query, hero_id, game_mode, start_date, end_date)

        matches = query.all()

        if not matches:
            return self._empty_player_stats()

        total_matches = len(matches)
        wins = sum(1 for m in matches if m.radiant_team == m.radiant_win)
        losses = total_matches - wins

        return PlayerStats(
            total_matches=total_matches,
            total_wins=wins,
            total_losses=losses,
            win_rate=(wins / total_matches * 100) if total_matches > 0 else 0,
            avg_kills=sum(m.kills or 0 for m in matches) / total_matches,
            avg_deaths=sum(m.deaths or 0 for m in matches) / total_matches,
            avg_assists=sum(m.assists or 0 for m in matches) / total_matches,
            avg_kda=self._calculate_avg_kda(matches),
            avg_gpm=sum(m.gold_per_min or 0 for m in matches) / total_matches if any(m.gold_per_min for m in matches) else None,
            avg_xpm=sum(m.xp_per_min or 0 for m in matches) / total_matches if any(m.xp_per_min for m in matches) else None,
            most_played_heroes=self.get_hero_stats(user_id, limit=5),
            recent_matches=total_matches,
            last_match_time=max(m.start_time for m in matches if m.start_time).isoformat() if any(m.start_time for m in matches) else None,
        )

    def get_hero_stats(
        self,
        user_id: int,
        hero_id: Optional[int] = None,
        game_mode: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[HeroStats]:
        """Get per-hero statistics"""
        # Only query matches with details (not stubs)
        query = self.db.query(Match).filter(
            Match.user_id == user_id,
            Match.has_details == True
        )
        query = self._apply_filters(query, hero_id, game_mode, start_date, end_date)

        matches = query.all()

        # Group by hero
        hero_data: Dict[int, List[Match]] = {}
        for match in matches:
            if match.hero_id not in hero_data:
                hero_data[match.hero_id] = []
            hero_data[match.hero_id].append(match)

        # Calculate stats per hero
        hero_stats = []
        for hero_id, hero_matches in hero_data.items():
            total_games = len(hero_matches)
            wins = sum(1 for m in hero_matches if m.radiant_team == m.radiant_win)
            losses = total_games - wins

            hero_stats.append(HeroStats(
                hero_id=hero_id,
                games_played=total_games,
                wins=wins,
                losses=losses,
                win_rate=(wins / total_games * 100) if total_games > 0 else 0,
                avg_kills=sum(m.kills or 0 for m in hero_matches) / total_games,
                avg_deaths=sum(m.deaths or 0 for m in hero_matches) / total_games,
                avg_assists=sum(m.assists or 0 for m in hero_matches) / total_games,
                avg_kda=self._calculate_avg_kda(hero_matches),
                avg_gpm=sum(m.gold_per_min or 0 for m in hero_matches) / total_games if any(m.gold_per_min for m in hero_matches) else None,
                avg_xpm=sum(m.xp_per_min or 0 for m in hero_matches) / total_games if any(m.xp_per_min for m in hero_matches) else None,
                total_hero_damage=sum(m.hero_damage or 0 for m in hero_matches),
                total_tower_damage=sum(m.tower_damage or 0 for m in hero_matches),
                total_hero_healing=sum(m.hero_healing or 0 for m in hero_matches),
            ))

        # Sort by games played
        hero_stats.sort(key=lambda x: x.games_played, reverse=True)

        if limit:
            hero_stats = hero_stats[:limit]

        return hero_stats

    def get_players_encountered(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[PlayerEncounteredStats]:
        """Get frequently played with players"""
        players = (
            self.db.query(PlayerEncountered)
            .filter(PlayerEncountered.user_id == user_id)
            .order_by(desc(PlayerEncountered.games_together))
            .limit(limit)
            .all()
        )

        return [
            PlayerEncounteredStats(
                account_id=p.account_id,
                persona_name=p.persona_name,
                games_together=p.games_together,
                games_won=p.games_won,
                games_lost=p.games_lost,
                win_rate=(p.games_won / p.games_together * 100) if p.games_together > 0 else 0,
            )
            for p in players
        ]

    def get_time_based_stats(
        self,
        user_id: int,
        periods: List[str] = ["daily", "weekly", "monthly", "3months", "6months", "12months"]
    ) -> List[TimeStats]:
        """Get time-based statistics"""
        now = datetime.utcnow()
        stats = []

        for period in periods:
            start_date = self._get_period_start_date(now, period)
            matches = (
                self.db.query(Match)
                .filter(
                    Match.user_id == user_id,
                    Match.start_time >= start_date
                )
                .all()
            )

            if not matches:
                continue

            total_games = len(matches)
            wins = sum(1 for m in matches if m.radiant_team == m.radiant_win)

            stats.append(TimeStats(
                period=period,
                start_date=start_date.isoformat(),
                end_date=now.isoformat(),
                total_games=total_games,
                wins=wins,
                losses=total_games - wins,
                win_rate=(wins / total_games * 100) if total_games > 0 else 0,
                avg_kills=sum(m.kills for m in matches) / total_games,
                avg_deaths=sum(m.deaths for m in matches) / total_games,
                avg_assists=sum(m.assists for m in matches) / total_games,
                avg_kda=self._calculate_avg_kda(matches),
                avg_gpm=sum(m.gold_per_min or 0 for m in matches) / total_games if any(m.gold_per_min for m in matches) else None,
                avg_xpm=sum(m.xp_per_min or 0 for m in matches) / total_games if any(m.xp_per_min for m in matches) else None,
            ))

        return stats

    def get_dashboard_stats(self, user_id: int) -> DashboardStats:
        """Get all dashboard statistics"""
        return DashboardStats(
            player_stats=self.get_player_stats(user_id),
            hero_stats=self.get_hero_stats(user_id, limit=10),
            players_encountered=self.get_players_encountered(user_id, limit=20),
            time_stats=self.get_time_based_stats(user_id),
        )

    def _apply_filters(
        self,
        query,
        hero_id: Optional[int],
        game_mode: Optional[int],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ):
        """Apply common filters to query"""
        if hero_id:
            query = query.filter(Match.hero_id == hero_id)
        if game_mode:
            query = query.filter(Match.game_mode == game_mode)
        if start_date:
            query = query.filter(Match.start_time >= start_date)
        if end_date:
            query = query.filter(Match.start_time <= end_date)
        return query

    @staticmethod
    def _calculate_avg_kda(matches: List[Match]) -> float:
        """Calculate average KDA ratio"""
        if not matches:
            return 0.0

        total_kda = 0.0
        valid_matches = 0
        for match in matches:
            # Skip stub matches with no data
            if match.kills is None or match.deaths is None or match.assists is None:
                continue

            valid_matches += 1
            if match.deaths == 0:
                total_kda += float(match.kills + match.assists)
            else:
                total_kda += (match.kills + match.assists) / match.deaths

        return total_kda / valid_matches if valid_matches > 0 else 0.0

    @staticmethod
    def _get_period_start_date(now: datetime, period: str) -> datetime:
        """Get start date for a time period"""
        if period == "daily":
            return now - timedelta(days=1)
        elif period == "weekly":
            return now - timedelta(weeks=1)
        elif period == "monthly":
            return now - timedelta(days=30)
        elif period == "3months":
            return now - timedelta(days=90)
        elif period == "6months":
            return now - timedelta(days=180)
        elif period == "12months":
            return now - timedelta(days=365)
        return now

    @staticmethod
    def _empty_player_stats() -> PlayerStats:
        """Return empty player stats"""
        return PlayerStats(
            total_matches=0,
            total_wins=0,
            total_losses=0,
            win_rate=0.0,
            avg_kills=0.0,
            avg_deaths=0.0,
            avg_assists=0.0,
            avg_kda=0.0,
            avg_gpm=None,
            avg_xpm=None,
            most_played_heroes=[],
            recent_matches=0,
            last_match_time=None,
        )
