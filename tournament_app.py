import streamlit as st
import pandas as pd
import io
import itertools
import math
import copy
import plotly.graph_objects as go
from typing import List, Optional

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

# Your original bracket visualization class from lib/bracket_viz.py
# Your original bracket visualization class from lib/bracket_viz.py
class BracketViz:
    def __init__(self, teams):
        self.numTeams = len(teams)
        self.teams = list(teams)
        self.max = len(max(["Round "]+teams, key=len)) if teams else 10
        self.numRounds = int(math.ceil(math.log(self.numTeams, 2))+1) if self.numTeams > 0 else 1
        self.totalNumTeams = int(2**math.ceil(math.log(self.numTeams, 2))) if self.numTeams > 0 else 0
        self.totalTeams = self.addTeams()
        self.lineup = ["bye" if "-" in str(x) else x for x in self.totalTeams]
        self.numToName()
        self.count = 0
        self.rounds = []
        for i in range(0, self.numRounds):
            self.rounds.append([])
            for _ in range(0, 2**(self.numRounds-i-1)):
                self.rounds[i].append("-"*self.max)
        if self.totalTeams:
            self.rounds[0] = list(self.totalTeams)
    
    def numToName(self):
        for i in range(0, self.numTeams):
            if (i+1) in self.totalTeams:
                self.totalTeams[self.totalTeams.index(i+1)] = self.teams[i]
    
    def shuffle(self):
        import random
        random.shuffle(self.teams)
        self.totalTeams = self.addTeams()
        self.numToName()
        self.rounds[0] = list(self.totalTeams)
    
    def update(self, round_num, winners):
        """Update winners for a specific round"""
        if round_num < 2 or round_num > len(self.rounds):
            return False
        
        prev_round_idx = round_num - 2  # Previous round (0-indexed)
        current_round_idx = round_num - 1  # Current round (0-indexed)
        
        # Get the teams from previous round
        prev_round_teams = self.rounds[prev_round_idx]
        
        # For each winner provided
        for winner in winners:
            winner_str = str(winner)
            
            # Find the winner in the previous round
            winner_found = False
            for i, team in enumerate(prev_round_teams):
                if str(team).lower() == winner_str.lower():
                    # Calculate which match this belongs to (pairs of teams)
                    match_idx = i // 2
                    
                    # Make sure we have enough slots in current round
                    while len(self.rounds[current_round_idx]) <= match_idx:
                        self.rounds[current_round_idx].append("-" * self.max)
                    
                    # Update the winner
                    self.rounds[current_round_idx][match_idx] = team
                    winner_found = True
                    break
            
            if not winner_found:
                return False
        
        # Check if current round is complete (no TBD entries)
        current_round = self.rounds[current_round_idx]
        for team in current_round:
            if str(team).startswith('-'):
                return False
        
        return True

    def advance_winner(self, from_round, match_idx, winner_name):
        """Advance a specific winner from one round to the next"""
        if from_round < 1 or from_round >= len(self.rounds):
            return False
            
        current_round_idx = from_round - 1
        next_round_idx = from_round
        
        # Ensure next round exists and has enough slots
        while len(self.rounds) <= next_round_idx:
            self.rounds.append([])
        
        # Calculate how many teams should be in next round
        current_teams = len([t for t in self.rounds[current_round_idx] if not str(t).startswith('-')])
        next_round_size = current_teams // 2
        
        while len(self.rounds[next_round_idx]) < next_round_size:
            self.rounds[next_round_idx].append("-" * self.max)
        
        # Find the winner in current round and advance them
        for i, team in enumerate(self.rounds[current_round_idx]):
            if str(team).lower() == winner_name.lower():
                target_slot = match_idx
                if target_slot < len(self.rounds[next_round_idx]):
                    self.rounds[next_round_idx][target_slot] = team
                    return True
        
        return False
    
    def addTeams(self):
        if self.numTeams == 0:
            return []
            
        x = self.numTeams
        teams = [1]
        temp = []
        count = 0
        for i in range(2, x+1):
            temp.append(i)
        for i in range(0, int(2**math.ceil(math.log(x, 2))-x)):
            temp.append("-"*self.max)
        for _ in range(0, int(math.ceil(math.log(x, 2)))):
            high = max(teams) if teams else 1
            for i in range(0, len(teams)):
                index = teams.index(high)+1
                if count < len(temp):
                    teams.insert(index, temp[count])
                high -= 1
                count += 1
        return teams
    
    def create_graph_visualization(self):
        """Create a proper tournament bracket visualization"""
        if self.numTeams == 0:
            fig = go.Figure()
            fig.update_layout(
                title="No bracket to display",
                showlegend=False,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='white',
                height=400
            )
            return fig
        
        fig = go.Figure()
        
        # Calculate bracket dimensions
        bracket_height = len(self.rounds[0]) * 60  # Height based on first round teams
        bracket_width = self.numRounds * 200
        
        # Colors for different states
        colors = {
            'active': '#4ECDC4',      # Teal for active players
            'winner': '#FFD700',      # Gold for winners
            'tbd': '#E0E0E0',         # Gray for TBD
            'group_placeholder': '#FFE5B4'  # Light orange for group placeholders
        }
        
        # Track all elements to draw
        rectangles = []
        texts = []
        lines = []
        
        # Process each round
        for round_idx in range(self.numRounds):
            teams_in_round = self.rounds[round_idx]
            num_teams = len(teams_in_round)
            
            if num_teams == 0:
                continue
                
            # Calculate positions for this round
            round_x = round_idx * 200 + 100
            
            # Calculate vertical spacing
            if num_teams == 1:
                # Final winner - center it
                y_positions = [bracket_height / 2]
            else:
                # Distribute teams vertically
                spacing = bracket_height / (num_teams + 1)
                y_positions = [spacing * (i + 1) for i in range(num_teams)]
            
            # Draw team boxes for this round
            for team_idx, (team, y_pos) in enumerate(zip(teams_in_round, y_positions)):
                team_str = str(team)
                
                # Determine color and display text
                if team_str.startswith('-'):
                    color = colors['tbd']
                    display_text = "TBD"
                elif "Group" in team_str:
                    color = colors['group_placeholder']
                    display_text = team_str.replace(' place', '').replace('Group ', 'G')
                elif round_idx == self.numRounds - 1:
                    color = colors['winner']
                    display_text = f"🏆 {team_str}"
                else:
                    color = colors['active']
                    display_text = team_str
                
                # Add rectangle for team box
                rectangles.append({
                    'x0': round_x - 80,
                    'x1': round_x + 80,
                    'y0': y_pos - 20,
                    'y1': y_pos + 20,
                    'fillcolor': color,
                    'line': {'color': '#333333', 'width': 2}
                })
                
                # Add text
                texts.append({
                    'x': round_x,
                    'y': y_pos,
                    'text': display_text,
                    'font': {'size': 10, 'color': 'black', 'family': 'Arial'},
                    'showarrow': False,
                    'xanchor': 'center',
                    'yanchor': 'middle'
                })
                
                # Draw connecting lines to next round
                if round_idx < self.numRounds - 1:
                    next_round_teams = self.rounds[round_idx + 1]
                    next_num_teams = len(next_round_teams)
                    
                    if next_num_teams > 0:
                        # Calculate which team in next round this connects to
                        next_team_idx = team_idx // 2
                        
                        if next_team_idx < next_num_teams:
                            # Calculate next round position
                            next_round_x = (round_idx + 1) * 200 + 100
                            
                            if next_num_teams == 1:
                                next_y = bracket_height / 2
                            else:
                                next_spacing = bracket_height / (next_num_teams + 1)
                                next_y = next_spacing * (next_team_idx + 1)
                            
                            # Draw horizontal line from current team
                            mid_x = round_x + 80 + (next_round_x - round_x - 160) / 2
                            
                            lines.extend([
                                # Horizontal line from team box
                                {'x0': round_x + 80, 'x1': mid_x, 'y0': y_pos, 'y1': y_pos},
                                # Vertical connector (if needed)
                                {'x0': mid_x, 'x1': mid_x, 'y0': y_pos, 'y1': next_y},
                                # Horizontal line to next round
                                {'x0': mid_x, 'x1': next_round_x - 80, 'y0': next_y, 'y1': next_y}
                            ])
        
        # Add all rectangles
        for rect in rectangles:
            fig.add_shape(
                type="rect",
                **rect
            )
        
        # Add all lines
        for line in lines:
            fig.add_shape(
                type="line",
                line={'color': '#666666', 'width': 2},
                **line
            )
        
        # Add all text annotations
        for text in texts:
            fig.add_annotation(**text)
        
        # Add round labels
        for round_idx in range(self.numRounds):
            round_x = round_idx * 200 + 100
            if round_idx == self.numRounds - 1:
                round_name = "Final"
            elif round_idx == self.numRounds - 2:
                round_name = "Semi-Final"
            elif round_idx == self.numRounds - 3:
                round_name = "Quarter-Final"
            else:
                round_name = f"Round {round_idx + 1}"
            
            fig.add_annotation(
                x=round_x,
                y=bracket_height + 40,
                text=f"<b>{round_name}</b>",
                font={'size': 12, 'color': '#333333'},
                showarrow=False,
                xanchor='center'
            )
        
        # Update layout
        fig.update_layout(
            title={
                'text': "Tournament Bracket",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': '#333333'}
            },
            showlegend=False,
            xaxis=dict(
                showgrid=False, 
                zeroline=False, 
                showticklabels=False, 
                fixedrange=True,
                range=[-50, bracket_width + 50]
            ),
            yaxis=dict(
                showgrid=False, 
                zeroline=False, 
                showticklabels=False, 
                fixedrange=True,
                range=[-50, bracket_height + 100]
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=max(400, bracket_height + 150),
            width=max(600, bracket_width + 100),
            margin=dict(l=20, r=20, t=60, b=20)
        )
        
        return fig

class Bracket:
    def __init__(self, groups, num_advance=2):
        self.groups = groups
        self.num_advance = num_advance
        self.more_advance_group_size = None
        self.fewer_advance_group_size = None

    @staticmethod
    def _snake_seed_groups(players, preferred_group_size, group_rounding_strat='up'):
        players_copy = players.copy()  # Don't modify original list
        players_copy.sort(key=lambda p: -1 * p.rating)
        
        q, r = divmod(len(players_copy), preferred_group_size)
        num_groups = 0
        if group_rounding_strat == 'up':
            num_groups = q
        elif group_rounding_strat == 'down':
            num_groups = q
            if r > 0:
                num_groups += 1
        else:
            raise ValueError('group_rounding_strat must be one of ("up", "down")')

        if num_groups == 0:
            return []

        groups = []
        for _ in range(num_groups):
            groups.append([])
        
        num_players = len(players_copy)
        for i in range(num_players):
            group_idx = i % num_groups
            if group_idx == 0 and i > 0:
                groups.reverse()
            p = players_copy.pop(0)
            groups[group_idx].append(p)

        return groups

    @classmethod
    def from_players_list(cls, players, preferred_group_size=4, group_rounding_strat='up'):
        if not players:
            return cls(groups=[])
            
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
    
    def display(self):
        """Create bracket visualization using improved graph display"""
        team_labels = []
        place_suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
        
        # Build team labels same way as your original code
        fewer_advance_size = None
        max_players_advance = self.num_advance
        if self.more_advance_group_size is not None:
            max_players_advance += 1
            fewer_advance_size = self.more_advance_group_size - 1
        if self.fewer_advance_group_size is not None:
            fewer_advance_size = self.fewer_advance_group_size
        
        for n in range(max_players_advance):
            for group in self.groups:
                if fewer_advance_size is not None and len(group.players) == fewer_advance_size:
                    if self.more_advance_group_size is not None and n + 1 > self.num_advance:
                        continue
                    elif self.fewer_advance_group_size is not None and n + 1 > self.num_advance - 1:
                        continue

                place = n + 1
                place_suffix = place_suffixes.get(place, 'th')
                label = f'Group {group.group_number} {place}{place_suffix} place'
                team_labels.append(label)
        
        # Return the enhanced BracketViz instead of the original one
        return BracketViz(team_labels)

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
    if 'bracket_viz' not in st.session_state:
        st.session_state.bracket_viz = None
    if 'players' not in st.session_state:
        st.session_state.players = []
    if 'group_winners' not in st.session_state:
        st.session_state.group_winners = {}
    
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
                st.session_state.bracket_viz = bracket.display()
                st.session_state.group_winners = {}
                
                st.success("Tournament generated successfully!")
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("Round Robin Groups")
        
        if st.session_state.bracket and st.session_state.bracket.groups:
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
                
                # Show players in group with winner selection
                col_players, col_winners = st.columns([2, 1])
                
                with col_players:
                    player_df = pd.DataFrame([
                        {
                            'Seed': letters[i], 
                            'Player': player.name, 
                            'Rating': player.rating
                        } 
                        for i, player in enumerate(group.players)
                    ])
                    st.dataframe(player_df, use_container_width=True, hide_index=True)
                
                with col_winners:
                    st.write("**Group Winners:**")
                    # Add winner selection for each advancing position
                    for place in range(1, num_advance + 1):
                        place_suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(place, 'th')
                        
                        # Get current winner if set
                        current_winner = None
                        if (group.group_number in st.session_state.group_winners and
                            place in st.session_state.group_winners[group.group_number]):
                            current_winner = st.session_state.group_winners[group.group_number][place]
                        
                        player_options = [""] + [player.name for player in group.players]
                        current_index = 0
                        if current_winner in player_options:
                            current_index = player_options.index(current_winner)
                        
                        winner = st.selectbox(
                            f"{place}{place_suffix} place:",
                            options=player_options,
                            index=current_index,
                            key=f"group_{group.group_number}_place_{place}"
                        )
                        
                        if winner:
                            if group.group_number not in st.session_state.group_winners:
                                st.session_state.group_winners[group.group_number] = {}
                            st.session_state.group_winners[group.group_number][place] = winner
                            
                            # Update the bracket visualization with actual player names
                            if st.session_state.bracket_viz:
                                # Find the team label and replace with actual name
                                place_suffix_str = {1: 'st', 2: 'nd', 3: 'rd'}.get(place, 'th')
                                team_label = f'Group {group.group_number} {place}{place_suffix_str} place'
                                if team_label in st.session_state.bracket_viz.rounds[0]:
                                    idx = st.session_state.bracket_viz.rounds[0].index(team_label)
                                    st.session_state.bracket_viz.rounds[0][idx] = winner
                
                # Show match schedule (collapsed by default)
                with st.expander("View Match Schedule"):
                    player_letters = letters[0:len(group.players)]
                    matches = make_rr_matches(player_letters)
                    
                    for i, (p1, p2) in enumerate(matches):
                        st.write(f"{i + 1}. **{p1}** vs **{p2}**")
                
                st.divider()
        else:
            st.info("👈 Configure tournament settings and generate bracket to see groups")
    
    with col2:
        st.header("Tournament Bracket")
        
        if st.session_state.bracket_viz:
            # Display bracket as interactive graph
            bracket_fig = st.session_state.bracket_viz.create_graph_visualization()
            st.plotly_chart(bracket_fig, use_container_width=True)
            
            # Show bracket controls below the graph
            st.subheader("Bracket Controls")
            
            # Show matches that need winners selected
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
                        
                        # Only show matches where both teams are real players (not placeholders or TBD)
                        if (not str(team1).startswith('-') and not str(team2).startswith('-') and 
                            "Group" not in str(team1) and "Group" not in str(team2)):
                            
                            current_winner = current_round[match_idx]
                            
                            if str(current_winner).startswith('-'):
                                matches_to_resolve.append({
                                    'round': round_num,
                                    'match': match_idx,
                                    'team1': str(team1),
                                    'team2': str(team2)
                                })
            
            if matches_to_resolve:
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
                            # Use the original update method from BracketViz
                            success = st.session_state.bracket_viz.update(match['round'], [winner])
                            if success:
                                st.rerun()
            
            # Show final winner if tournament is complete
            final_round = st.session_state.bracket_viz.rounds[-1] if st.session_state.bracket_viz.rounds else []
            if final_round and not str(final_round[0]).startswith('-'):
                st.success(f"🏆 **Tournament Champion: {final_round[0]}** 🏆")
                st.balloons()
            elif not matches_to_resolve:
                # Check if we're waiting for group winners
                waiting_for_groups = False
                if st.session_state.bracket_viz.rounds:
                    for team in st.session_state.bracket_viz.rounds[0]:
                        if "Group" in str(team):
                            waiting_for_groups = True
                            break
                
                if waiting_for_groups:
                    st.info("👈 Complete group play to unlock bracket matches!")
                else:
                    st.info("All matches resolved!")
            
        else:
            st.info("Generate a tournament to see the bracket visualization")
    
    # Download functionality
    if st.session_state.bracket and st.session_state.bracket.groups:
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