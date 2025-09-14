import streamlit as st
import pandas as pd
import io
import itertools
import math
import copy
from typing import List, Optional

# Import your existing classes (assuming they're available)
# If running standalone, you'll need to copy the classes here

class Player:
    def __init__(self, name, rating):
        self.name = name
        self.rating = rating

    def __repr__(self):
        return f'Player({self.name}, {self.rating})'

class Group:
    def __init__(self, players, group_number):
        self.players = players
        self.group_number = group_number

    def get_max_rating(self):
        return sorted(self.players, key=lambda p: p.rating)[-1].rating

class InteractiveBracket:
    """Enhanced bracket class for Streamlit with interactive winner selection"""
    def __init__(self, teams):
        self.numTeams = len(teams)
        self.teams = list(teams)
        self.max = max(15, len(max(["Round "]+teams, key=len)))
        self.numRounds = int(math.ceil(math.log(self.numTeams, 2)) + 1)
        self.totalNumTeams = int(2**math.ceil(math.log(self.numTeams, 2)))
        self.totalTeams = self.addTeams()
        self.lineup = ["bye" if "-" in str(x) else x for x in self.totalTeams]
        self.numToName()
        self.rounds = []
        for i in range(0, self.numRounds):
            self.rounds.append([])
            for _ in range(0, 2**(self.numRounds-i-1)):
                self.rounds[i].append("-"*self.max)
        self.rounds[0] = list(self.totalTeams)
    
    def numToName(self):
        for i in range(0, self.numTeams):
            if (i+1) in self.totalTeams:
                self.totalTeams[self.totalTeams.index(i+1)] = self.teams[i]
    
    def addTeams(self):
        x = self.numTeams
        teams = [1]
        temp = []
        count = 0
        for i in range(2, x+1):
            temp.append(i)
        for i in range(0, int(2**math.ceil(math.log(x, 2))-x)):
            temp.append("-"*self.max)
        for _ in range(0, int(math.ceil(math.log(x, 2)))):
            high = max(teams)
            for i in range(0, len(teams)):
                index = teams.index(high)+1
                teams.insert(index, temp[count])
                high -= 1
                count += 1
        return teams
    
    def update_winner(self, round_num, match_index, winner):
        """Update a winner for a specific match"""
        if round_num < len(self.rounds) - 1:
            self.rounds[round_num][match_index] = winner
            return True
        return False
    
    def get_bracket_structure(self):
        """Return bracket structure for display"""
        return {
            'rounds': self.rounds,
            'numRounds': self.numRounds,
            'lineup': self.lineup
        }

class Bracket:
    def __init__(self, groups, num_advance=2):
        self.groups = groups
        self.num_advance = num_advance
        self.more_advance_group_size = None
        self.fewer_advance_group_size = None

    @staticmethod
    def _snake_seed_groups(players, preferred_group_size, group_rounding_strat='up'):
        players.sort(key=lambda p: -1 * p.rating)
        q, r = divmod(len(players), preferred_group_size)
        num_groups = 0
        if group_rounding_strat == 'up':
            num_groups = q
        elif group_rounding_strat == 'down':
            num_groups = q
            if r > 0:
                num_groups += 1
        else:
            raise ValueError('group_rounding_strat must be one of ("up", "down")')

        groups = [] 
        for _ in range(num_groups):
            groups.append([])
        
        num_players = len(players)
        for i in range(num_players):
            group_idx = i % num_groups
            if group_idx == 0:
                groups.reverse()
            p = players.pop(0)
            groups[group_idx].append(p)

        return groups

    @classmethod
    def from_players_list(cls, players, preferred_group_size=4, group_rounding_strat='up'):
        groups = cls._snake_seed_groups(
            players=players,
            preferred_group_size=preferred_group_size,
            group_rounding_strat=group_rounding_strat
        )

        groups = [sorted(g, key=lambda p: -1 * p.rating) for g in groups]
        groups = [Group(players=g, group_number=0) for g in groups]
        groups = sorted(groups, key=lambda g: -1 * g.get_max_rating())
        for i, g in enumerate(groups):
            g.group_number = i + 1
        
        return cls(groups=groups)

def make_rr_matches(letters):
    pairs = list(itertools.combinations(letters, 2))
    matches = []
    for i in range(len(pairs)):
        if i % 2 == 0:
            pair = pairs.pop(0)
        else:
            pair = pairs.pop(-1)
        matches.append(pair)
    matches.reverse()
    return matches

def main():
    st.set_page_config(page_title="Tournament Bracket Manager", layout="wide")
    
    st.title("🏆 Tournament Bracket Manager")
    st.markdown("Create seeded groups and tournament brackets with real-time winner editing")
    
    # Initialize session state
    if 'bracket' not in st.session_state:
        st.session_state.bracket = None
    if 'interactive_bracket' not in st.session_state:
        st.session_state.interactive_bracket = None
    if 'players' not in st.session_state:
        st.session_state.players = []
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Tournament Configuration")
        
        # Player input methods
        input_method = st.radio("Player Input Method:", ["Manual Entry", "CSV Upload"])
        
        if input_method == "Manual Entry":
            st.subheader("Add Players")
            with st.form("add_player"):
                player_name = st.text_input("Player Name")
                player_rating = st.number_input("Rating", min_value=0, max_value=3000, value=1500)
                submitted = st.form_submit_button("Add Player")
                
                if submitted and player_name:
                    new_player = Player(player_name, int(player_rating))
                    st.session_state.players.append(new_player)
                    st.success(f"Added {player_name} (Rating: {player_rating})")
        
        elif input_method == "CSV Upload":
            st.subheader("Upload CSV File")
            uploaded_file = st.file_uploader(
                "Choose CSV file", 
                type=['csv'],
                help="CSV should have columns: player_name, rating, confirmed (Y/N)"
            )
            
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    if 'confirmed' in df.columns:
                        confirmed_players = df[df['confirmed'].str.strip() == 'Y']
                    else:
                        confirmed_players = df
                    
                    st.session_state.players = []
                    for _, row in confirmed_players.iterrows():
                        player = Player(row['player_name'], int(row['rating']))
                        st.session_state.players.append(player)
                    
                    st.success(f"Loaded {len(st.session_state.players)} players")
                except Exception as e:
                    st.error(f"Error reading CSV: {e}")
        
        # Show current players
        if st.session_state.players:
            st.subheader("Current Players")
            for i, player in enumerate(st.session_state.players):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"{player.name} ({player.rating})")
                with col2:
                    if st.button("❌", key=f"remove_{i}"):
                        st.session_state.players.pop(i)
                        st.rerun()
        
        st.divider()
        
        # Group configuration
        st.subheader("Group Settings")
        group_size = st.slider("Preferred Group Size", min_value=2, max_value=8, value=4)
        group_rounding = st.selectbox("Group Rounding Strategy", ["up", "down"])
        num_advance = st.number_input("Players Advancing per Group", min_value=1, max_value=4, value=2)
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            fewer_advance_size = st.number_input(
                "Group size with 1 fewer advance", 
                min_value=0, max_value=8, value=0,
                help="If group size equals this value, 1 fewer player advances"
            )
            more_advance_size = st.number_input(
                "Group size with 1 more advance", 
                min_value=0, max_value=8, value=0,
                help="If group size equals this value, 1 more player advances"
            )
        
        # Generate bracket button
        if st.button("🎯 Generate Tournament", type="primary"):
            if len(st.session_state.players) < 4:
                st.error("Need at least 4 players to generate tournament")
            else:
                # Create bracket
                bracket = Bracket.from_players_list(
                    st.session_state.players.copy(),
                    preferred_group_size=group_size,
                    group_rounding_strat=group_rounding
                )
                bracket.num_advance = num_advance
                if fewer_advance_size > 0:
                    bracket.fewer_advance_group_size = fewer_advance_size
                if more_advance_size > 0:
                    bracket.more_advance_group_size = more_advance_size
                
                st.session_state.bracket = bracket
                
                # Create interactive bracket from group winners
                team_labels = []
                place_suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
                
                max_players_advance = num_advance
                if more_advance_size > 0:
                    max_players_advance += 1
                
                for n in range(max_players_advance):
                    for group in bracket.groups:
                        place = n + 1
                        place_suffix = place_suffixes.get(place, 'th')
                        
                        # Check advancement rules
                        group_advances = num_advance
                        if fewer_advance_size > 0 and len(group.players) == fewer_advance_size:
                            group_advances -= 1
                        elif more_advance_size > 0 and len(group.players) == more_advance_size:
                            group_advances += 1
                        
                        if place <= group_advances:
                            label = f'Group {group.group_number} {place}{place_suffix} place'
                            team_labels.append(label)
                
                if team_labels:
                    st.session_state.interactive_bracket = InteractiveBracket(team_labels)
                
                st.success("Tournament generated successfully!")
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("Round Robin Groups")
        
        if st.session_state.bracket:
            letters = ['A', 'B', 'C', 'D', 'E']
            
            for group in st.session_state.bracket.groups:
                # Calculate number advancing for this group
                num_advance = st.session_state.bracket.num_advance
                if (st.session_state.bracket.more_advance_group_size and 
                    len(group.players) == st.session_state.bracket.more_advance_group_size):
                    num_advance += 1
                elif (st.session_state.bracket.fewer_advance_group_size and 
                      len(group.players) == st.session_state.bracket.fewer_advance_group_size):
                    num_advance -= 1
                
                st.subheader(f"Group {group.group_number} - Top {num_advance} Advance")
                
                # Show players in group
                player_df = pd.DataFrame([
                    {
                        'Seed': letters[i], 
                        'Player': player.name, 
                        'Rating': player.rating
                    } 
                    for i, player in enumerate(group.players)
                ])
                st.dataframe(player_df, use_container_width=True)
                
                # Show match schedule
                st.write("**Match Schedule:**")
                player_letters = letters[0:len(group.players)]
                matches = make_rr_matches(player_letters)
                
                match_text = ""
                for i, (p1, p2) in enumerate(matches):
                    match_text += f"{i + 1}. {p1} vs {p2}\\n"
                
                st.text(match_text)
                st.divider()
        else:
            st.info("👈 Configure tournament settings and generate bracket to see groups")
    
    with col2:
        st.header("Tournament Bracket")
        
        if st.session_state.interactive_bracket:
            bracket_data = st.session_state.interactive_bracket.get_bracket_structure()
            
            # Display bracket with interactive winner selection
            st.subheader("Bracket Progress")
            
            # Show rounds
            for round_num in range(len(bracket_data['rounds'])):
                if round_num == 0:
                    st.write(f"**Round 1 (Initial Seeding)**")
                    teams_in_round = [team for team in bracket_data['rounds'][0] if not team.startswith('-')]
                    for i, team in enumerate(teams_in_round):
                        st.text(f"{i+1:2d}. {team}")
                else:
                    st.write(f"**Round {round_num + 1}**")
                    
                    # Show matches for this round
                    prev_round = bracket_data['rounds'][round_num - 1]
                    current_round = bracket_data['rounds'][round_num]
                    
                    for match_idx in range(len(current_round)):
                        # Get the two teams for this match
                        team1_idx = match_idx * 2
                        team2_idx = match_idx * 2 + 1
                        
                        if team1_idx < len(prev_round) and team2_idx < len(prev_round):
                            team1 = prev_round[team1_idx]
                            team2 = prev_round[team2_idx]
                            
                            # Skip if either team is a placeholder
                            if team1.startswith('-') or team2.startswith('-'):
                                continue
                            
                            col_a, col_b = st.columns([3, 1])
                            
                            with col_a:
                                st.write(f"**Match {match_idx + 1}:** {team1} vs {team2}")
                            
                            with col_b:
                                # Winner selection
                                current_winner = current_round[match_idx]
                                if not current_winner.startswith('-'):
                                    st.success(f"✓ {current_winner}")
                                else:
                                    winner = st.selectbox(
                                        "Winner:",
                                        options=["", team1, team2],
                                        key=f"round_{round_num}_match_{match_idx}"
                                    )
                                    
                                    if winner:
                                        st.session_state.interactive_bracket.update_winner(
                                            round_num, match_idx, winner
                                        )
                                        st.rerun()
                
                st.divider()
            
            # Show final winner
            final_round = bracket_data['rounds'][-1]
            if final_round and not final_round[0].startswith('-'):
                st.balloons()
                st.success(f"🏆 **Tournament Winner: {final_round[0]}** 🏆")
        else:
            st.info("Generate a tournament to see the bracket visualization")
    
    # Download functionality
    if st.session_state.bracket:
        st.header("Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Export Group Results"):
                # Create export data
                export_data = []
                for group in st.session_state.bracket.groups:
                    for i, player in enumerate(group.players):
                        export_data.append({
                            'Group': group.group_number,
                            'Seed': ['A', 'B', 'C', 'D', 'E'][i],
                            'Player': player.name,
                            'Rating': player.rating
                        })
                
                df = pd.DataFrame(export_data)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="💾 Download CSV",
                    data=csv,
                    file_name="tournament_groups.csv",
                    mime="text/csv"
                )
        
        with col2:
            st.info("Bracket export functionality coming soon!")

if __name__ == "__main__":
    main()