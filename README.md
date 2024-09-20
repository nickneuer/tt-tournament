## About

Generate seeded groups and tournament bracket from a list of players. Player input should be CSV of the form `player_name, rating, confirmed` where `confirmed` should be `Y` for attending players

## Usage
```
usage: bracket.py [-h] [-g GROUP_SIZE] [-r GROUP_ROUNDING] [-i INPUT_FILE] [-n NUM_ADVANCE] [-f FEWER_ADVANCE_FOR_GRP_SIZE] [-m MORE_ADVANCE_FOR_GRP_SIZE] [-d]

options:
  -h, --help            show this help message and exit
  -g GROUP_SIZE, --group_size GROUP_SIZE
                        preferred group size to use for RR groups
  -r GROUP_ROUNDING, --group_rounding GROUP_ROUNDING
                        allowed values ('up', 'down'). A value of 'up' allows for groups greater than preferred group size, 'down' allows for smaller
  -i INPUT_FILE, --input_file INPUT_FILE
                        input csv file of player 'name', 'rating'
  -n NUM_ADVANCE, --num_advance NUM_ADVANCE
                        number of players that advance to the main draw from each RR group
  -f FEWER_ADVANCE_FOR_GRP_SIZE, --fewer_advance_for_grp_size FEWER_ADVANCE_FOR_GRP_SIZE
                        if group size == <this param> 1 fewer player advances
  -m MORE_ADVANCE_FOR_GRP_SIZE, --more_advance_for_grp_size MORE_ADVANCE_FOR_GRP_SIZE
                        if group size == <this param> 1 more player advances
  -d, --display_rating  number of players that advance to the main draw from each RR group
```

## Example
`python3 bracket.py -i input/confirmed_players.csv -n 1 -g 3 -r 'up' -m 4`

*Output:*
```
TOTAL GROUPS: 7

GROUP 1 - top 1 advance
----------------------------------------
A) Anthony Chu
B) Anthony Szumilo
C) Alan Li

  1. A vs C
  2. B vs C
  3. A vs B

GROUP 2 - top 1 advance
----------------------------------------
A) Andy Lin
B) Minghao Chen
C) Lev Markus

  1. A vs C
  2. B vs C
  3. A vs B

GROUP 3 - top 1 advance
----------------------------------------
A) William Craig
B) Daniel Man
C) Riley Woo

  1. A vs C
  2. B vs C
  3. A vs B

GROUP 4 - top 1 advance
----------------------------------------
A) Austin Wu-Duenas
B) Dan Ohlsen
C) Chris Zuttler

  1. A vs C
  2. B vs C
  3. A vs B

GROUP 5 - top 1 advance
----------------------------------------
A) James Zhang
B) Hanson Qin
C) Eric Aki

  1. A vs C
  2. B vs C
  3. A vs B

GROUP 6 - top 2 advance
----------------------------------------
A) Rahul Chatwani
B) Nick Neuer
C) Sam Maurer
D) Jenna Kiyasu

  1. B vs C
  2. A vs D
  3. B vs D
  4. A vs C
  5. C vs D
  6. A vs B

GROUP 7 - top 2 advance
----------------------------------------
A) Jabari Jourdan-Ali
B) Michael Mendelson
C) Matthew Styczynski
D) Anna Fita

  1. B vs C
  2. A vs D
  3. B vs D
  4. A vs C
  5. C vs D
  6. A vs B


Seed              Round 1             Round 2             Round 3             Round 4             Round 5
   1   Group 1 1st place \
                           ----------------- \
 bye   ----------------- /
                                               ----------------- \
   8   Group 6 2nd place \
                           ----------------- /
   9   Group 7 2nd place /
                                                                   ----------------- \
   4   Group 4 1st place \
                           ----------------- \
 bye   ----------------- /
                                               ----------------- /
   5   Group 5 1st place \
                           ----------------- /
 bye   ----------------- /
                                                                                       -----------------
   2   Group 2 1st place \
                           ----------------- \
 bye   ----------------- /
                                               ----------------- \
   7   Group 7 1st place \
                           ----------------- /
 bye   ----------------- /
                                                                   ----------------- /
   3   Group 3 1st place \
                           ----------------- \
 bye   ----------------- /
                                               ----------------- /
   6   Group 6 1st place \
                           ----------------- /
 bye   ----------------- /


```
