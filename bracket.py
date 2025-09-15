import json
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
                    if round_idx == 0:
                        display_text = "BYE"
                        teams_in_round[team_idx] = "BYE"
                    else:
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


def load_players_file(players_file):
    players = []
    with open(players_file) as f:
        reader = csv.reader(f)
        for row in reader:
            if row[2].strip() == 'Y':
                players.append(Player(row[0], int(row[1])))

    return players


if __name__ == '__main__':
    import csv
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-g', "--group_size", default=4, type=int, help="preferred group size to use for RR groups") 
    parser.add_argument('-r', "--group_rounding", default='up', help="allowed values ('up', 'down'). A value of 'up' allows for groups greater than preferred group size, 'down' allows for smaller")
    parser.add_argument('-i', "--input_file", default='input/players.csv', help="input csv file of player 'name', 'rating'")
    parser.add_argument('-n', "--num_advance", default=2, type=int, help="number of players that advance to the main draw from each RR group")
    parser.add_argument('-f', "--fewer_advance_for_grp_size", type=int, help="if group size == <this param> 1 fewer player advances")
    parser.add_argument('-m', "--more_advance_for_grp_size", type=int, help="if group size == <this param> 1 more player advances")
    parser.add_argument('-d', "--display_rating", action='store_true', help="number of players that advance to the main draw from each RR group")

    args = parser.parse_args()

    players = load_players_file(args.input_file)

    bracket = Bracket.from_players_list(
        players, 
        preferred_group_size=args.group_size,
        group_rounding_strat=args.group_rounding
    )
    bracket.num_advance = args.num_advance
    # set any exceptions for group size and num_advance
    if args.fewer_advance_for_grp_size:
        bracket.fewer_advance_group_size = args.fewer_advance_for_grp_size
    if args.more_advance_for_grp_size:
        bracket.more_advance_group_size = args.more_advance_for_grp_size
    bracket.print_groups(display_rating=args.display_rating)
    print()
    bracket.display()
    print()
