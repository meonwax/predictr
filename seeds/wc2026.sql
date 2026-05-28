--
-- 2026 FIFA World Cup - full tournament seed
--
-- Tournament: 11 June - 19 July 2026, hosted by Canada / Mexico / USA
-- 48 teams . 12 groups (A-L) . 104 matches . 16 venues
--
-- Sources:
--   * FIFA "FWC26 Match Schedule" (English) - match numbers and kickoff times in Eastern Time
--     https://digitalhub.fifa.com/m/1be9ce37eb98fcc5/original/FWC26-Match-Schedule_English.pdf
--   * Wikipedia "2026 FIFA World Cup" (final draw 5 Dec 2025) - venues per match
--     https://en.wikipedia.org/wiki/2026_FIFA_World_Cup
--
-- Conventions:
--   * All `kickoff_time` values are UTC.
--     ET kickoff + 4 h = UTC (June/July -> EDT = UTC-4).
--   * Team IDs are 3-letter FIFA country codes, lowercased to match the existing data style.
--   * Group IDs are 'a'..'l' for the group stage; knockout pseudo-groups are
--     'r32' (Round of 32), 'r16' (Round of 16), 'qf' (Quarter-finals),
--     'sf' (Semi-finals), '3rd' (Third-place play-off) and 'fin' (Final).
--     NOTE: this requires `groups.id` to be widened from CHAR(1) to VARCHAR(4)
--     (handled by the Alembic migration that ships with this seed).
--   * Knockout fixtures store NULL for `team_home_id` / `team_away_id` until
--     the bracket fills in (same pattern as the previous Euro 2024 seed).
--

--
-- Groups (12 group-stage + 6 knockout pseudo-groups)
--
INSERT INTO groups (id, priority) VALUES
  ('a',    0),
  ('b',    1),
  ('c',    2),
  ('d',    3),
  ('e',    4),
  ('f',    5),
  ('g',    6),
  ('h',    7),
  ('i',    8),
  ('j',    9),
  ('k',   10),
  ('l',   11),
  ('r32', 12),
  ('r16', 13),
  ('qf',  14),
  ('sf',  15),
  ('3rd', 16),
  ('fin', 17);

--
-- Teams (48 - FIFA 3-letter codes, lowercased)
--
INSERT INTO team (id, group_id) VALUES
  -- Group A
  ('mex', 'a'), ('rsa', 'a'), ('kor', 'a'), ('cze', 'a'),
  -- Group B
  ('can', 'b'), ('bih', 'b'), ('qat', 'b'), ('sui', 'b'),
  -- Group C
  ('bra', 'c'), ('mar', 'c'), ('hai', 'c'), ('sco', 'c'),
  -- Group D
  ('usa', 'd'), ('par', 'd'), ('aus', 'd'), ('tur', 'd'),
  -- Group E
  ('ger', 'e'), ('cuw', 'e'), ('civ', 'e'), ('ecu', 'e'),
  -- Group F
  ('ned', 'f'), ('jpn', 'f'), ('swe', 'f'), ('tun', 'f'),
  -- Group G
  ('bel', 'g'), ('egy', 'g'), ('irn', 'g'), ('nzl', 'g'),
  -- Group H
  ('esp', 'h'), ('cpv', 'h'), ('ksa', 'h'), ('uru', 'h'),
  -- Group I
  ('fra', 'i'), ('sen', 'i'), ('irq', 'i'), ('nor', 'i'),
  -- Group J
  ('arg', 'j'), ('alg', 'j'), ('aut', 'j'), ('jor', 'j'),
  -- Group K
  ('por', 'k'), ('cod', 'k'), ('uzb', 'k'), ('col', 'k'),
  -- Group L
  ('eng', 'l'), ('cro', 'l'), ('gha', 'l'), ('pan', 'l');

--
-- Venues (16 host stadiums in 16 host cities)
--
-- city codes are short, application-internal labels; they don't have to match ISO.
--
INSERT INTO venue (id, stadium, city) VALUES
  ( 1, 'Mercedes-Benz Stadium, Atlanta, USA',           'atl'),
  ( 2, 'Gillette Stadium, Foxborough, USA',             'bos'),
  ( 3, 'AT&T Stadium, Arlington, USA',                  'dal'),
  ( 4, 'Estadio Akron, Zapopan, MEX',                   'gdl'),
  ( 5, 'NRG Stadium, Houston, USA',                     'hou'),
  ( 6, 'Arrowhead Stadium, Kansas City, USA',           'kc'),
  ( 7, 'SoFi Stadium, Inglewood, USA',                  'la'),
  ( 8, 'Estadio Azteca, Mexico City, MEX',              'mex'),
  ( 9, 'Hard Rock Stadium, Miami Gardens, USA',         'mia'),
  (10, 'Estadio BBVA, Guadalupe, MEX',                  'mty'),
  (11, 'MetLife Stadium, East Rutherford, USA',         'nyj'),
  (12, 'Lincoln Financial Field, Philadelphia, USA',    'phi'),
  (13, 'Levi''s Stadium, Santa Clara, USA',             'sfo'),
  (14, 'Lumen Field, Seattle, USA',                     'sea'),
  (15, 'BMO Field, Toronto, CAN',                       'tor'),
  (16, 'BC Place, Vancouver, CAN',                      'van');

--
-- Games (104)
--
-- Times are UTC. Eastern Time + 4h = UTC during the tournament window.
--
-- Group stage - Matchday 1 (matches 1-24, 11-17 June)
--
INSERT INTO game (id, kickoff_time, group_id, venue_id, team_home_id, team_away_id) VALUES
  (  1, '2026-06-11 19:00:00', 'a',  8, 'mex', 'rsa'),  -- Mexico v South Africa,    Estadio Azteca,          15:00 ET
  (  2, '2026-06-12 02:00:00', 'a',  4, 'kor', 'cze'),  -- Korea Rep v Czechia,      Estadio Akron,           22:00 ET (Jun 11)

  (  3, '2026-06-12 19:00:00', 'b', 15, 'can', 'bih'),  -- Canada v Bosnia & H,      BMO Field,               15:00 ET
  (  4, '2026-06-13 01:00:00', 'd',  7, 'usa', 'par'),  -- USA v Paraguay,           SoFi Stadium,            21:00 ET (Jun 12)

  (  5, '2026-06-14 01:00:00', 'c',  2, 'hai', 'sco'),  -- Haiti v Scotland,         Gillette Stadium,        21:00 ET (Jun 13)
  (  6, '2026-06-13 04:00:00', 'd', 16, 'aus', 'tur'),  -- Australia v Türkiye,      BC Place,                00:00 ET (Jun 13)
  (  7, '2026-06-13 22:00:00', 'c', 11, 'bra', 'mar'),  -- Brazil v Morocco,         MetLife Stadium,         18:00 ET
  (  8, '2026-06-13 19:00:00', 'b', 13, 'qat', 'sui'),  -- Qatar v Switzerland,      Levi''s Stadium,         15:00 ET

  (  9, '2026-06-14 23:00:00', 'e', 12, 'civ', 'ecu'),  -- Côte d''Ivoire v Ecuador, Lincoln Financial Field, 19:00 ET
  ( 10, '2026-06-14 17:00:00', 'e',  5, 'ger', 'cuw'),  -- Germany v Curaçao,        NRG Stadium,             13:00 ET
  ( 11, '2026-06-14 20:00:00', 'f',  3, 'ned', 'jpn'),  -- Netherlands v Japan,      AT&T Stadium,            16:00 ET
  ( 12, '2026-06-15 02:00:00', 'f', 10, 'swe', 'tun'),  -- Sweden v Tunisia,         Estadio BBVA,            22:00 ET (Jun 14)

  ( 13, '2026-06-15 22:00:00', 'h',  9, 'ksa', 'uru'),  -- Saudi Arabia v Uruguay,   Hard Rock Stadium,       18:00 ET
  ( 14, '2026-06-15 16:00:00', 'h',  1, 'esp', 'cpv'),  -- Spain v Cape Verde,       Mercedes-Benz Stadium,   12:00 ET
  ( 15, '2026-06-16 01:00:00', 'g',  7, 'irn', 'nzl'),  -- Iran v New Zealand,       SoFi Stadium,            21:00 ET (Jun 15)
  ( 16, '2026-06-15 19:00:00', 'g', 14, 'bel', 'egy'),  -- Belgium v Egypt,          Lumen Field,             15:00 ET

  ( 17, '2026-06-16 19:00:00', 'i', 11, 'fra', 'sen'),  -- France v Senegal,         MetLife Stadium,         15:00 ET
  ( 18, '2026-06-16 22:00:00', 'i',  2, 'irq', 'nor'),  -- Iraq v Norway,            Gillette Stadium,        18:00 ET
  ( 19, '2026-06-17 01:00:00', 'j',  6, 'arg', 'alg'),  -- Argentina v Algeria,      Arrowhead Stadium,       21:00 ET (Jun 16)
  ( 20, '2026-06-17 04:00:00', 'j', 13, 'aut', 'jor'),  -- Austria v Jordan,         Levi''s Stadium,         00:00 ET (Jun 17)

  ( 21, '2026-06-17 23:00:00', 'l', 15, 'gha', 'pan'),  -- Ghana v Panama,           BMO Field,               19:00 ET
  ( 22, '2026-06-17 20:00:00', 'l',  3, 'eng', 'cro'),  -- England v Croatia,        AT&T Stadium,            16:00 ET
  ( 23, '2026-06-17 17:00:00', 'k',  5, 'por', 'cod'),  -- Portugal v DR Congo,      NRG Stadium,             13:00 ET
  ( 24, '2026-06-18 02:00:00', 'k',  8, 'uzb', 'col'),  -- Uzbekistan v Colombia,    Estadio Azteca,          22:00 ET (Jun 17)

--
-- Group stage - Matchday 2 (matches 25-48, 18-23 June)
--
  ( 25, '2026-06-18 16:00:00', 'a',  1, 'cze', 'rsa'),  -- Czechia v South Africa,   Mercedes-Benz Stadium,   12:00 ET
  ( 26, '2026-06-18 19:00:00', 'b',  7, 'sui', 'bih'),  -- Switzerland v Bosnia,     SoFi Stadium,            15:00 ET
  ( 27, '2026-06-18 22:00:00', 'b', 16, 'can', 'qat'),  -- Canada v Qatar,           BC Place,                18:00 ET
  ( 28, '2026-06-19 01:00:00', 'a',  4, 'mex', 'kor'),  -- Mexico v Korea Republic,  Estadio Akron,           21:00 ET (Jun 18)

  ( 29, '2026-06-20 00:30:00', 'c', 12, 'bra', 'hai'),  -- Brazil v Haiti,           Lincoln Financial Field, 20:30 ET (Jun 19)
  ( 30, '2026-06-19 22:00:00', 'c',  2, 'sco', 'mar'),  -- Scotland v Morocco,       Gillette Stadium,        18:00 ET
  ( 31, '2026-06-20 03:00:00', 'd', 13, 'tur', 'par'),  -- Türkiye v Paraguay,       Levi''s Stadium,         23:00 ET (Jun 19)
  ( 32, '2026-06-19 19:00:00', 'd', 14, 'usa', 'aus'),  -- USA v Australia,          Lumen Field,             15:00 ET

  ( 33, '2026-06-20 20:00:00', 'e', 15, 'ger', 'civ'),  -- Germany v Côte d''Ivoire, BMO Field,               16:00 ET
  ( 34, '2026-06-21 00:00:00', 'e',  6, 'ecu', 'cuw'),  -- Ecuador v Curaçao,        Arrowhead Stadium,       20:00 ET (Jun 20)
  ( 35, '2026-06-20 17:00:00', 'f',  5, 'ned', 'swe'),  -- Netherlands v Sweden,     NRG Stadium,             13:00 ET
  ( 36, '2026-06-21 04:00:00', 'f', 10, 'tun', 'jpn'),  -- Tunisia v Japan,          Estadio BBVA,            00:00 ET (Jun 21)

  ( 37, '2026-06-21 22:00:00', 'h',  9, 'uru', 'cpv'),  -- Uruguay v Cape Verde,     Hard Rock Stadium,       18:00 ET
  ( 38, '2026-06-21 16:00:00', 'h',  1, 'esp', 'ksa'),  -- Spain v Saudi Arabia,     Mercedes-Benz Stadium,   12:00 ET
  ( 39, '2026-06-21 19:00:00', 'g',  7, 'bel', 'irn'),  -- Belgium v Iran,           SoFi Stadium,            15:00 ET
  ( 40, '2026-06-22 01:00:00', 'g', 16, 'nzl', 'egy'),  -- New Zealand v Egypt,      BC Place,                21:00 ET (Jun 21)

  ( 41, '2026-06-23 00:00:00', 'i', 11, 'nor', 'sen'),  -- Norway v Senegal,         MetLife Stadium,         20:00 ET (Jun 22)
  ( 42, '2026-06-22 21:00:00', 'i', 12, 'fra', 'irq'),  -- France v Iraq,            Lincoln Financial Field, 17:00 ET
  ( 43, '2026-06-22 17:00:00', 'j',  3, 'arg', 'aut'),  -- Argentina v Austria,      AT&T Stadium,            13:00 ET
  ( 44, '2026-06-23 03:00:00', 'j', 13, 'jor', 'alg'),  -- Jordan v Algeria,         Levi''s Stadium,         23:00 ET (Jun 22)

  ( 45, '2026-06-23 20:00:00', 'l',  2, 'eng', 'gha'),  -- England v Ghana,          Gillette Stadium,        16:00 ET
  ( 46, '2026-06-23 23:00:00', 'l', 15, 'pan', 'cro'),  -- Panama v Croatia,         BMO Field,               19:00 ET
  ( 47, '2026-06-23 17:00:00', 'k',  5, 'por', 'uzb'),  -- Portugal v Uzbekistan,    NRG Stadium,             13:00 ET
  ( 48, '2026-06-24 02:00:00', 'k',  4, 'col', 'cod'),  -- Colombia v DR Congo,      Estadio Akron,           22:00 ET (Jun 23)

--
-- Group stage - Matchday 3 (matches 49-72, 24-27 June, all simultaneous within a group)
--
  ( 49, '2026-06-24 22:00:00', 'c',  9, 'sco', 'bra'),  -- Scotland v Brazil,        Hard Rock Stadium,       18:00 ET
  ( 50, '2026-06-24 22:00:00', 'c',  1, 'mar', 'hai'),  -- Morocco v Haiti,          Mercedes-Benz Stadium,   18:00 ET
  ( 51, '2026-06-24 19:00:00', 'b', 16, 'sui', 'can'),  -- Switzerland v Canada,     BC Place,                15:00 ET
  ( 52, '2026-06-24 19:00:00', 'b', 14, 'bih', 'qat'),  -- Bosnia & H. v Qatar,      Lumen Field,             15:00 ET
  ( 53, '2026-06-25 01:00:00', 'a',  8, 'cze', 'mex'),  -- Czechia v Mexico,         Estadio Azteca,          21:00 ET (Jun 24)
  ( 54, '2026-06-25 01:00:00', 'a', 10, 'rsa', 'kor'),  -- South Africa v Korea Rep, Estadio BBVA,            21:00 ET (Jun 24)

  ( 55, '2026-06-25 20:00:00', 'e', 12, 'cuw', 'civ'),  -- Curaçao v Côte d''Ivoire, Lincoln Financial Field, 16:00 ET
  ( 56, '2026-06-25 20:00:00', 'e', 11, 'ecu', 'ger'),  -- Ecuador v Germany,        MetLife Stadium,         16:00 ET
  ( 57, '2026-06-25 23:00:00', 'f',  3, 'jpn', 'swe'),  -- Japan v Sweden,           AT&T Stadium,            19:00 ET
  ( 58, '2026-06-25 23:00:00', 'f',  6, 'tun', 'ned'),  -- Tunisia v Netherlands,    Arrowhead Stadium,       19:00 ET
  ( 59, '2026-06-26 02:00:00', 'd',  7, 'tur', 'usa'),  -- Türkiye v USA,            SoFi Stadium,            22:00 ET (Jun 25)
  ( 60, '2026-06-26 02:00:00', 'd', 13, 'par', 'aus'),  -- Paraguay v Australia,     Levi''s Stadium,         22:00 ET (Jun 25)

  ( 61, '2026-06-26 19:00:00', 'i',  2, 'nor', 'fra'),  -- Norway v France,          Gillette Stadium,        15:00 ET
  ( 62, '2026-06-26 19:00:00', 'i', 15, 'sen', 'irq'),  -- Senegal v Iraq,           BMO Field,               15:00 ET
  ( 63, '2026-06-27 03:00:00', 'g', 14, 'egy', 'irn'),  -- Egypt v Iran,             Lumen Field,             23:00 ET (Jun 26)
  ( 64, '2026-06-27 03:00:00', 'g', 16, 'nzl', 'bel'),  -- New Zealand v Belgium,    BC Place,                23:00 ET (Jun 26)
  ( 65, '2026-06-27 00:00:00', 'h',  5, 'cpv', 'ksa'),  -- Cape Verde v Saudi A.,    NRG Stadium,             20:00 ET (Jun 26)
  ( 66, '2026-06-27 00:00:00', 'h',  4, 'uru', 'esp'),  -- Uruguay v Spain,          Estadio Akron,           20:00 ET (Jun 26)

  ( 67, '2026-06-27 21:00:00', 'l', 11, 'pan', 'eng'),  -- Panama v England,         MetLife Stadium,         17:00 ET
  ( 68, '2026-06-27 21:00:00', 'l', 12, 'cro', 'gha'),  -- Croatia v Ghana,          Lincoln Financial Field, 17:00 ET
  ( 69, '2026-06-28 02:00:00', 'j',  6, 'alg', 'aut'),  -- Algeria v Austria,        Arrowhead Stadium,       22:00 ET (Jun 27)
  ( 70, '2026-06-28 02:00:00', 'j',  3, 'jor', 'arg'),  -- Jordan v Argentina,       AT&T Stadium,            22:00 ET (Jun 27)
  ( 71, '2026-06-27 23:30:00', 'k',  9, 'col', 'por'),  -- Colombia v Portugal,      Hard Rock Stadium,       19:30 ET
  ( 72, '2026-06-27 23:30:00', 'k',  1, 'cod', 'uzb');  -- DR Congo v Uzbekistan,    Mercedes-Benz Stadium,   19:30 ET

--
-- Knockout - Round of 32 (matches 73-88, 28 June - 3 July).
-- Team slots are NULL; the admin enters them as group standings settle.
-- The ``placeholder_*`` columns carry the human-readable bracket slot:
--   '1A'  = winner of group A
--   '2C'  = runner-up of group C
--   '3 ABCDF' = one of the best four 3rd-placed teams from those groups
--   'W74' = winner of match 74
--   'L101' = loser of semi-final 101 (third-place play-off only)
--
INSERT INTO game (id, kickoff_time, group_id, venue_id, team_home_id, team_away_id, placeholder_home, placeholder_away) VALUES
  ( 73, '2026-06-28 19:00:00', 'r32',  7, NULL, NULL, '2A', '2B'),       -- SoFi Stadium,            15:00 ET
  ( 74, '2026-06-29 20:30:00', 'r32',  2, NULL, NULL, '1E', '3 ABCDF'),  -- Gillette Stadium,        16:30 ET
  ( 75, '2026-06-30 01:00:00', 'r32', 10, NULL, NULL, '1F', '2C'),       -- Estadio BBVA,            21:00 ET (Jun 29)
  ( 76, '2026-06-29 17:00:00', 'r32',  5, NULL, NULL, '1C', '2F'),       -- NRG Stadium,             13:00 ET
  ( 77, '2026-06-30 21:00:00', 'r32', 11, NULL, NULL, '1I', '3 CDFGH'),  -- MetLife Stadium,         17:00 ET
  ( 78, '2026-06-30 17:00:00', 'r32',  3, NULL, NULL, '2E', '2I'),       -- AT&T Stadium,            13:00 ET
  ( 79, '2026-07-01 01:00:00', 'r32',  8, NULL, NULL, '1A', '3 CEFHI'),  -- Estadio Azteca,          21:00 ET (Jun 30)
  ( 80, '2026-07-01 16:00:00', 'r32',  1, NULL, NULL, '1L', '3 EHIJK'),  -- Mercedes-Benz Stadium,   12:00 ET
  ( 81, '2026-07-02 00:00:00', 'r32', 13, NULL, NULL, '1D', '3 BEFIJ'),  -- Levi''s Stadium,         20:00 ET (Jul 1)
  ( 82, '2026-07-01 20:00:00', 'r32', 14, NULL, NULL, '1G', '3 AEHIJ'),  -- Lumen Field,             16:00 ET
  ( 83, '2026-07-02 23:00:00', 'r32', 15, NULL, NULL, '2K', '2L'),       -- BMO Field,               19:00 ET
  ( 84, '2026-07-02 19:00:00', 'r32',  7, NULL, NULL, '1H', '2J'),       -- SoFi Stadium,            15:00 ET
  ( 85, '2026-07-03 03:00:00', 'r32', 16, NULL, NULL, '1B', '3 EFGIJ'),  -- BC Place,                23:00 ET (Jul 2)
  ( 86, '2026-07-03 22:00:00', 'r32',  9, NULL, NULL, '1J', '2H'),       -- Hard Rock Stadium,       18:00 ET
  ( 87, '2026-07-04 01:30:00', 'r32',  6, NULL, NULL, '1K', '3 DEIJL'),  -- Arrowhead Stadium,       21:30 ET (Jul 3)
  ( 88, '2026-07-03 18:00:00', 'r32',  3, NULL, NULL, '2D', '2G'),       -- AT&T Stadium,            14:00 ET

--
-- Knockout - Round of 16 (matches 89-96, 4-7 July)
--
  ( 89, '2026-07-04 21:00:00', 'r16', 12, NULL, NULL, 'W74', 'W77'),     -- Lincoln Financial Field, 17:00 ET
  ( 90, '2026-07-04 17:00:00', 'r16',  5, NULL, NULL, 'W73', 'W75'),     -- NRG Stadium,             13:00 ET
  ( 91, '2026-07-05 20:00:00', 'r16', 11, NULL, NULL, 'W76', 'W78'),     -- MetLife Stadium,         16:00 ET
  ( 92, '2026-07-06 00:00:00', 'r16',  8, NULL, NULL, 'W79', 'W80'),     -- Estadio Azteca,          20:00 ET (Jul 5)
  ( 93, '2026-07-06 19:00:00', 'r16',  3, NULL, NULL, 'W83', 'W84'),     -- AT&T Stadium,            15:00 ET
  ( 94, '2026-07-07 00:00:00', 'r16', 14, NULL, NULL, 'W81', 'W82'),     -- Lumen Field,             20:00 ET (Jul 6)
  ( 95, '2026-07-07 16:00:00', 'r16',  1, NULL, NULL, 'W86', 'W88'),     -- Mercedes-Benz Stadium,   12:00 ET
  ( 96, '2026-07-07 20:00:00', 'r16', 16, NULL, NULL, 'W85', 'W87'),     -- BC Place,                16:00 ET

--
-- Knockout - Quarter-finals (matches 97-100, 9-11 July)
--
  ( 97, '2026-07-09 20:00:00', 'qf',   2, NULL, NULL, 'W89', 'W90'),     -- Gillette Stadium,        16:00 ET
  ( 98, '2026-07-10 19:00:00', 'qf',   7, NULL, NULL, 'W93', 'W94'),     -- SoFi Stadium,            15:00 ET
  ( 99, '2026-07-11 21:00:00', 'qf',   9, NULL, NULL, 'W91', 'W92'),     -- Hard Rock Stadium,       17:00 ET
  (100, '2026-07-12 01:00:00', 'qf',   6, NULL, NULL, 'W95', 'W96'),     -- Arrowhead Stadium,       21:00 ET (Jul 11)

--
-- Knockout - Semi-finals (matches 101-102, 14-15 July)
--
  (101, '2026-07-14 19:00:00', 'sf',   3, NULL, NULL, 'W97', 'W98'),     -- AT&T Stadium,            15:00 ET
  (102, '2026-07-15 19:00:00', 'sf',   1, NULL, NULL, 'W99', 'W100'),    -- Mercedes-Benz Stadium,   15:00 ET

--
-- Knockout - Third-place play-off (match 103, 18 July)
--
  (103, '2026-07-18 21:00:00', '3rd',  9, NULL, NULL, 'L101', 'L102'),   -- Hard Rock Stadium,       17:00 ET

--
-- Knockout - Final (match 104, 19 July)
--
  (104, '2026-07-19 19:00:00', 'fin', 11, NULL, NULL, 'W101', 'W102');   -- MetLife Stadium,         15:00 ET

--
-- Site-wide configuration (singleton row).
--
-- ``rules_en`` is Markdown. The /info route runs it through Jinja2 first so
-- placeholders like {{ points_result }} resolve to the configured scoring
-- values, then converts it to HTML server-side. The {{ ... }} braces here
-- are intentionally NOT escaped - they're consumed by the Python template
-- engine at render time, not by Postgres.
--
INSERT INTO config (
  title, owner, admin_email, show_important_message,
  points_result, points_tendency_spread, points_tendency,
  rules_en, rules_de
) VALUES (
  'Predictr',
  'Predictr',
  'admin@example.com',
  false,
  5, 3, 2,
  E'## Welcome to **{{ title }}**\n\nThis is the prediction game for the 2026 FIFA World Cup - the first edition with **48 teams** spread over **12 groups**, **104 matches**, and the shiny new **Round of 32** knockout stage. The tournament kicks off on **11 June 2026** and ends with the final on **19 July 2026** at MetLife Stadium, New Jersey.\n\n## How to play\n\n1. Sign up with your name, email, and a password.\n2. Predict the **final score** of every match before kickoff. After kickoff the bet is locked - no edits allowed.\n3. Answer the **special questions** before each one''s individual deadline (top scorer of the tournament, dark-horse semi-finalist, etc.).\n4. Watch the **ladder** to see how you''re doing against the rest of the office.\n\n## Scoring\n\nFor every match your bet is compared against the official result:\n\n| Outcome                                            | Points                       |\n| -------------------------------------------------- | ---------------------------- |\n| **Exact score**                                    | **{{ points_result }}**      |\n| Correct goal difference (e.g. 2:1 vs 3:2)          | {{ points_tendency_spread }} |\n| Correct winner only (or correct draw)              | {{ points_tendency }}        |\n| Wrong tendency                                     | 0                            |\n\nFor special questions you get the **full point value of the question** if your answer matches the correct one (case-insensitive, comma-separated variants count as "the same answer"). Otherwise zero - there is no partial credit.\n\n## Tie-breaking on the ladder\n\nIf two players end up with the same total, the one with more **exact results** ranks higher. If they''re still tied, alphabetical order decides.\n\n## Questions or trouble?\n\nDrop a line to <a href="mailto:{{ admin_email }}">{{ admin_email }}</a>.\n',
  E'## Willkommen bei **{{ title }}**\n\nDas ist das Tippspiel für die FIFA Fussball-Weltmeisterschaft 2026 - die erste Ausgabe mit **48 Mannschaften** in **12 Gruppen**, **104 Spielen** und der neuen **Runde der letzten 32**. Das Turnier startet am **11. Juni 2026** und endet mit dem Finale am **19. Juli 2026** im MetLife Stadium in New Jersey.\n\n## Spielablauf\n\n1. Mit Name, E-Mail und Passwort registrieren.\n2. Vor jedem Anpfiff das **Endergebnis** tippen. Nach dem Anpfiff ist der Tipp gesperrt - keine Änderungen mehr möglich.\n3. Die **Sonderfragen** jeweils vor ihrem eigenen Stichtag beantworten (Torschützenkönig, Geheim-Halbfinalist, ...).\n4. In der **Rangliste** mitverfolgen, wie es im Vergleich zu den anderen läuft.\n\n## Punktevergabe\n\nPro Spiel wird der Tipp mit dem offiziellen Ergebnis verglichen:\n\n| Ergebnis                                       | Punkte                       |\n| ---------------------------------------------- | ---------------------------- |\n| **Exakter Endstand**                           | **{{ points_result }}**      |\n| Richtige Tordifferenz (z. B. 2:1 vs. 3:2)      | {{ points_tendency_spread }} |\n| Nur richtiger Sieger (oder richtiges Remis)    | {{ points_tendency }}        |\n| Falsche Tendenz                                | 0                            |\n\nBei Sonderfragen gibt es die **volle Punktzahl der Frage**, wenn die Antwort zur korrekten passt (Groß-/Kleinschreibung egal, komma-getrennte Varianten zählen als "dieselbe Antwort"). Sonst null Punkte - Teilpunkte gibt es nicht.\n\n## Gleichstand in der Rangliste\n\nBei Punktegleichstand liegt die Spielerin oder der Spieler mit **mehr exakten Ergebnissen** vorn. Bleibt es trotzdem gleich, entscheidet die alphabetische Reihenfolge.\n\n## Fragen oder Probleme?\n\nEine kurze Mail an <a href="mailto:{{ admin_email }}">{{ admin_email }}</a> genügt.\n'
);
