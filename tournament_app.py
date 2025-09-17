import streamlit as st
import pandas as pd
from typing import List, Optional, Dict, Any
from bracket import Bracket, make_rr_matches, Player


class TournamentState:
    """Manages tournament session state"""
    
    @staticmethod
    def initialize():
        """Initialize session state variables"""
        defaults = {
            'bracket': None,
            'bracket_viz': None,
            'players': [],
            'group_winners': {}
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    @staticmethod
    def add_player(name: str, rating: int) -> bool:
        """Add a player to the tournament"""
        if name:
            new_player = Player(name, rating)
            st.session_state.players.append(new_player)
            return True
        return False
    
    @staticmethod
    def remove_player(index: int):
        """Remove a player by index"""
        if 0 <= index < len(st.session_state.players):
            st.session_state.players.pop(index)
    
    @staticmethod
    def load_players_from_csv(df: pd.DataFrame) -> int:
        """Load players from CSV dataframe, return count loaded"""
        if 'confirmed' in df.columns:
            confirmed_players = df[df['confirmed'].str.strip() == 'going']
        else:
            confirmed_players = df
        
        st.session_state.players = []
        for _, row in confirmed_players.iterrows():
            player = Player(row['player_name'], int(row['rating']))
            st.session_state.players.append(player)
        
        return len(st.session_state.players)


class PlayerInputHandler:
    """Handles player input methods"""
    
    @staticmethod
    def render_manual_entry():
        """Render manual player entry form"""
        st.subheader("Add Players")
        with st.form("add_player"):
            player_name = st.text_input("Player Name")
            player_rating = st.number_input("Rating", min_value=0, max_value=3000, value=1500)
            submitted = st.form_submit_button("Add Player")
            
            if submitted and TournamentState.add_player(player_name, int(player_rating)):
                st.success(f"Added {player_name} (Rating: {player_rating})")
    
    @staticmethod
    def render_csv_upload():
        """Render CSV upload interface"""
        st.subheader("Upload CSV File")
        uploaded_file = st.file_uploader(
            "Choose CSV file", 
            type=['csv'],
            help="CSV should have columns: player_name, rating, confirmed (Y/N)"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                count = TournamentState.load_players_from_csv(df)
                st.success(f"Loaded {count} players")
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
    
    @staticmethod
    def render_player_list():
        """Render current players list with remove buttons"""
        if not st.session_state.players:
            return
            
        st.subheader("Current Players")
        for i, player in enumerate(st.session_state.players):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(f"{player.name} ({player.rating})")
            with col2:
                if st.button("❌", key=f"remove_{i}"):
                    TournamentState.remove_player(i)
                    st.rerun()


class TournamentConfig:
    """Handles tournament configuration"""
    
    @staticmethod
    def render_settings() -> Dict[str, Any]:
        """Render tournament settings and return configuration"""
        st.subheader("Group Settings")
        group_size = st.slider("Preferred Group Size", min_value=2, max_value=8, value=4)
        group_rounding = st.selectbox("Group Rounding Strategy", ["up", "down"])
        num_advance = st.number_input("Players Advancing per Group", min_value=1, max_value=4, value=2)
        
        # Advanced settings
        fewer_advance_size = 0
        more_advance_size = 0
        
        with st.expander("Advanced Settings"):
            fewer_advance_size = st.number_input(
                "Group size where 1 fewer player advances", 
                min_value=0, max_value=8, value=0,
                help="If group size equals this value, 1 fewer player advances"
            )
            more_advance_size = st.number_input(
                "Group size where 1 more player advance", 
                min_value=0, max_value=8, value=0,
                help="If group size equals this value, 1 more player advances"
            )
        
        return {
            'group_size': group_size,
            'group_rounding': group_rounding,
            'num_advance': num_advance,
            'fewer_advance_size': fewer_advance_size,
            'more_advance_size': more_advance_size
        }


class BracketGenerator:
    """Handles bracket generation"""
    
    @staticmethod
    def generate_tournament(config: Dict[str, Any]) -> bool:
        """Generate tournament bracket from configuration"""
        if len(st.session_state.players) < 4:
            st.error("Need at least 4 players to generate tournament")
            return False
        
        bracket = Bracket.from_players_list(
            st.session_state.players.copy(),
            preferred_group_size=config['group_size'],
            group_rounding_strat=config['group_rounding']
        )
        
        bracket.num_advance = config['num_advance']
        if config['fewer_advance_size'] > 0:
            bracket.fewer_advance_group_size = config['fewer_advance_size']
        if config['more_advance_size'] > 0:
            bracket.more_advance_group_size = config['more_advance_size']
        
        st.session_state.bracket = bracket
        st.session_state.bracket_viz = bracket.display()
        st.session_state.group_winners = {}
        
        st.success("Tournament generated successfully!")
        return True


class GroupManager:
    """Handles group display and winner selection"""
    
    @staticmethod
    def calculate_advancing_count(group, bracket) -> int:
        """Calculate how many players advance from a group"""
        num_advance = bracket.num_advance
        
        if (bracket.more_advance_group_size and 
            len(group.players) == bracket.more_advance_group_size):
            num_advance += 1
        elif (bracket.fewer_advance_group_size and 
              len(group.players) == bracket.fewer_advance_group_size):
            num_advance -= 1
        
        return num_advance
    
    @staticmethod
    def render_group_players(group) -> pd.DataFrame:
        """Render group players as dataframe"""
        letters = ['A', 'B', 'C', 'D', 'E']
        player_df = pd.DataFrame([
            {
                'Seed': letters[i], 
                'Player': player.name, 
                'Rating': player.rating
            } 
            for i, player in enumerate(group.players)
        ])
        return player_df
    
    @staticmethod
    def render_winner_selection(group, num_advance):
        """Render winner selection controls for a group"""
        st.write("**Group Winners:**")
        
        for place in range(1, num_advance + 1):
            place_suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(place, 'th')
            
            # Get current winner if set
            current_winner = GroupManager.get_current_winner(group.group_number, place)
            
            player_options = [""] + [player.name for player in group.players]
            current_index = player_options.index(current_winner) if current_winner in player_options else 0
            
            winner = st.selectbox(
                f"{place}{place_suffix} place:",
                options=player_options,
                index=current_index,
                key=f"group_{group.group_number}_place_{place}"
            )
            
            if winner:
                GroupManager.set_group_winner(group.group_number, place, winner)
                GroupManager.update_bracket_visualization(group.group_number, place, winner)
    
    @staticmethod
    def get_current_winner(group_number: int, place: int) -> Optional[str]:
        """Get current winner for a group and place"""
        if (group_number in st.session_state.group_winners and
            place in st.session_state.group_winners[group_number]):
            return st.session_state.group_winners[group_number][place]
        return None
    
    @staticmethod
    def set_group_winner(group_number: int, place: int, winner: str):
        """Set group winner"""
        if group_number not in st.session_state.group_winners:
            st.session_state.group_winners[group_number] = {}
        st.session_state.group_winners[group_number][place] = winner
    
    @staticmethod
    def update_bracket_visualization(group_number: int, place: int, winner: str):
        """Update bracket visualization with winner"""
        if not st.session_state.bracket_viz:
            return
            
        place_suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(place, 'th')
        team_label = f'Group {group_number} {place}{place_suffix} place'
        
        if team_label in st.session_state.bracket_viz.rounds[0]:
            idx = st.session_state.bracket_viz.rounds[0].index(team_label)
            st.session_state.bracket_viz.rounds[0][idx] = winner
    
    @staticmethod
    def render_match_schedule(group):
        """Render match schedule for a group"""
        with st.expander("View Match Schedule"):
            letters = ['A', 'B', 'C', 'D', 'E']
            player_letters = letters[0:len(group.players)]
            matches = make_rr_matches(player_letters)
            
            for i, (p1, p2) in enumerate(matches):
                st.write(f"{i + 1}. **{p1}** vs **{p2}**")
    
    @staticmethod
    def render_all_groups():
        """Render all tournament groups"""
        if not (st.session_state.bracket and st.session_state.bracket.groups):
            st.info("👈 Configure tournament settings and generate bracket to see groups")
            return
        
        for group in st.session_state.bracket.groups:
            num_advance = GroupManager.calculate_advancing_count(group, st.session_state.bracket)
            
            st.subheader(f"Group {group.group_number} - Top {num_advance} Advance")
            
            col_players, col_winners = st.columns([2, 1])
            
            with col_players:
                player_df = GroupManager.render_group_players(group)
                st.dataframe(player_df, use_container_width=True, hide_index=True)
            
            with col_winners:
                GroupManager.render_winner_selection(group, num_advance)
            
            GroupManager.render_match_schedule(group)
            st.divider()


class BracketManager:
    """Handles bracket visualization and match management"""
    
    @staticmethod
    def find_active_matches() -> List[Dict[str, Any]]:
        """Find matches that need winners selected"""
        if not st.session_state.bracket_viz:
            return []
        
        matches_to_resolve = []
        
        for round_num in range(2, st.session_state.bracket_viz.numRounds + 1):
            prev_round = st.session_state.bracket_viz.rounds[round_num - 2]
            current_round = st.session_state.bracket_viz.rounds[round_num - 1]
            
            for match_idx in range(len(current_round)):
                team1_idx = match_idx * 2
                team2_idx = match_idx * 2 + 1
                
                if (team1_idx < len(prev_round) and team2_idx < len(prev_round)):
                    team1 = prev_round[team1_idx]
                    team2 = prev_round[team2_idx]
                    current_winner = current_round[match_idx]
                    
                    # Only show matches where both teams are real players
                    if (BracketManager.is_real_player(team1) and BracketManager.is_real_player(team2) and 
                        str(current_winner).startswith('-')):
                        
                        matches_to_resolve.append({
                            'round': round_num,
                            'match': match_idx,
                            'team1': str(team1),
                            'team2': str(team2)
                        })
        
        return matches_to_resolve
    
    @staticmethod
    def is_real_player(team) -> bool:
        """Check if team is a real player (not placeholder)"""
        team_str = str(team)
        return not (team_str.startswith('-') or "Group" in team_str)
    
    @staticmethod
    def render_bracket_controls():
        """Render bracket match controls"""
        matches_to_resolve = BracketManager.find_active_matches()
        
        if not matches_to_resolve:
            BracketManager.check_tournament_status()
            return
        
        st.write("**Select Winners for Active Matches:**")
        
        for match in matches_to_resolve:
            col_match, col_winner = st.columns([2, 1])
            
            with col_match:
                st.write(f"**Round {match['round']}, Match {match['match'] + 1}:**")
                st.write(f"{match['team1']} vs {match['team2']}")
            
            with col_winner:
                winner = st.selectbox(
                    "Winner:",
                    options=["", match['team1'], match['team2']],
                    key=f"bracket_round_{match['round']}_match_{match['match']}"
                )
                
                if winner:
                    success = st.session_state.bracket_viz.update(match['round'], [winner])
                    if success:
                        st.rerun()
    
    @staticmethod
    def check_tournament_status():
        """Check and display tournament completion status"""
        if not st.session_state.bracket_viz or not st.session_state.bracket_viz.rounds:
            return
        
        final_round = st.session_state.bracket_viz.rounds[-1]
        
        if final_round and not str(final_round[0]).startswith('-'):
            st.success(f"🏆 **Tournament Champion: {final_round[0]}** 🏆")
            st.balloons()
        else:
            # Check if waiting for group winners
            waiting_for_groups = any("Group" in str(team) for team in st.session_state.bracket_viz.rounds[0])
            
            if waiting_for_groups:
                st.info("👈 Complete group play to unlock bracket matches!")
            else:
                st.info("All matches resolved!")


class ExportManager:
    """Handles data export functionality"""
    
    @staticmethod
    def render_export_options():
        """Render export options"""
        if not (st.session_state.bracket and st.session_state.bracket.groups):
            return
        
        st.header("Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Export Group Results"):
                csv_data = ExportManager.generate_group_csv()
                st.download_button(
                    label="💾 Download CSV",
                    data=csv_data,
                    file_name="tournament_groups.csv",
                    mime="text/csv"
                )
        
        with col2:
            st.info("Bracket export functionality coming soon!")
    
    @staticmethod
    def generate_group_csv() -> str:
        """Generate CSV data for group results"""
        export_data = []
        letters = ['A', 'B', 'C', 'D', 'E']
        
        for group in st.session_state.bracket.groups:
            for i, player in enumerate(group.players):
                export_data.append({
                    'Group': group.group_number,
                    'Seed': letters[i],
                    'Player': player.name,
                    'Rating': player.rating
                })
        
        df = pd.DataFrame(export_data)
        return df.to_csv(index=False)


def render_sidebar():
    """Render the sidebar with tournament configuration"""
    with st.sidebar:
        st.header("Tournament Configuration")
        
        # Player input methods
        input_method = st.radio("Player Input Method:", ["Manual Entry", "CSV Upload"])
        
        if input_method == "Manual Entry":
            PlayerInputHandler.render_manual_entry()
        else:
            PlayerInputHandler.render_csv_upload()
        
        PlayerInputHandler.render_player_list()
        st.divider()
        
        # Tournament configuration
        config = TournamentConfig.render_settings()
        
        # Generate bracket button
        if st.button("🎯 Generate Tournament", type="primary"):
            BracketGenerator.generate_tournament(config)


def render_main_content():
    """Render the main content area"""
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("Round Robin Groups")
        GroupManager.render_all_groups()
    
    with col2:
        st.header("Tournament Bracket")
        
        if st.session_state.bracket_viz:
            # Display bracket visualization
            bracket_fig = st.session_state.bracket_viz.create_graph_visualization()
            st.plotly_chart(bracket_fig, use_container_width=True)
            
            # Show bracket controls
            st.subheader("Bracket Controls")
            BracketManager.render_bracket_controls()
        else:
            st.info("Generate a tournament to see the bracket visualization")


def main():
    """Main application entry point"""
    st.set_page_config(page_title="Tournament Bracket Manager", layout="wide")
    
    st.title("🏆 Tournament Bracket Manager")
    st.markdown("Create seeded groups and tournament brackets with real-time winner editing")
    
    # Initialize session state
    TournamentState.initialize()
    
    # Render UI components
    render_sidebar()
    render_main_content()
    ExportManager.render_export_options()


if __name__ == "__main__":
    main()
