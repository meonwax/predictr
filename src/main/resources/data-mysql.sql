--
-- Euro 2016 data
--
INSERT IGNORE INTO `groups` (`id`, `priority`) VALUES
  ('a', 0),
  ('b', 1),
  ('c', 2),
  ('d', 3),
  ('e', 4),
  ('f', 5),
  ('8', 6),
  ('4', 7),
  ('2', 8),
  ('1', 9);

INSERT IGNORE INTO `team` (`id`, `group_id`) VALUES
  ('alb', 'a'),
  ('fra', 'a'),
  ('rou', 'a'),
  ('sui', 'a'),
  ('eng', 'b'),
  ('rus', 'b'),
  ('svk', 'b'),
  ('wal', 'b'),
  ('ger', 'c'),
  ('nir', 'c'),
  ('pol', 'c'),
  ('ukr', 'c'),
  ('cro', 'd'),
  ('cze', 'd'),
  ('esp', 'd'),
  ('tur', 'd'),
  ('bel', 'e'),
  ('ita', 'e'),
  ('irl', 'e'),
  ('swe', 'e'),
  ('aut', 'f'),
  ('hun', 'f'),
  ('isl', 'f'),
  ('por', 'f');

INSERT IGNORE INTO `locations` (`id`, `stadium`, `city`) VALUES
  ('sd', 'Stade de France', 'Saint-Denis'),
  ('le', 'Stade Bollaert-Delelis', 'Lens'),
  ('bo', 'Nouveau Stade de Bordeaux', 'Bordeaux'),
  ('ma', 'Stade Vélodrome', 'Marseille'),
  ('pa', 'Parc des Princes', 'Paris'),
  ('ni', 'Allianz Riviera', 'Nice'),
  ('li', 'Grand Stade Lille Métropole', 'Lille'),
  ('to', 'Stadium Municipal', 'Toulouse'),
  ('ly', 'Stade de Lyon', 'Lyon'),
  ('se', 'Geoffroy-Guichard', 'Saint-Etienne');

INSERT IGNORE INTO `game` (`id`, `kickoff_time`, `group_id`, `location_id`, `team_home_id`, `team_away_id`) VALUES
  -- Matchday 1
  (1, '2016-06-10 21:00:00', 'a', 'sd', 'fra', 'rou'),
  (2, '2016-06-11 15:00:00', 'a', 'le', 'alb', 'sui'),
  (3, '2016-06-11 18:00:00', 'b', 'bo', 'wal', 'svk'),
  (4, '2016-06-11 21:00:00', 'b', 'ma', 'eng', 'rus'),
  (5, '2016-06-12 15:00:00', 'd', 'pa', 'tur', 'cro'),
  (6, '2016-06-12 18:00:00', 'c', 'ni', 'pol', 'nir'),
  (7, '2016-06-12 21:00:00', 'c', 'li', 'ger', 'ukr'),
  (8, '2016-06-13 15:00:00', 'd', 'to', 'esp', 'cze'),
  (9, '2016-06-13 18:00:00', 'e', 'sd', 'irl', 'swe'),
  (10, '2016-06-13 21:00:00', 'e', 'ly', 'bel', 'ita'),
  (11, '2016-06-14 18:00:00', 'f', 'bo', 'aut', 'hun'),
  (12, '2016-06-14 21:00:00', 'f', 'se', 'por', 'isl'),

  -- Matchday 2
  (13, '2016-06-15 15:00:00', 'b', 'li', 'rus', 'svk'),
  (14, '2016-06-15 18:00:00', 'a', 'pa', 'rou', 'sui'),
  (15, '2016-06-15 21:00:00', 'a', 'ma', 'fra', 'alb'),
  (16, '2016-06-16 15:00:00', 'b', 'le', 'eng', 'wal'),
  (17, '2016-06-16 18:00:00', 'c', 'ly', 'ukr', 'nir'),
  (18, '2016-06-16 21:00:00', 'c', 'sd', 'ger', 'pol'),
  (19, '2016-06-17 15:00:00', 'e', 'to', 'ita', 'swe'),
  (20, '2016-06-17 18:00:00', 'd', 'se', 'cze', 'cro'),
  (21, '2016-06-17 21:00:00', 'd', 'ni', 'esp', 'tur'),
  (22, '2016-06-18 15:00:00', 'e', 'bo', 'bel', 'irl'),
  (23, '2016-06-18 18:00:00', 'f', 'ma', 'isl', 'hun'),
  (24, '2016-06-18 21:00:00', 'f', 'pa', 'por', 'aut'),

  -- Matchday 3
  (25, '2016-06-19 21:00:00', 'a', 'li', 'sui', 'fra'),
  (26, '2016-06-19 21:00:00', 'a', 'ly', 'rou', 'alb'),
  (27, '2016-06-20 21:00:00', 'b', 'se', 'svk', 'eng'),
  (28, '2016-06-20 21:00:00', 'b', 'to', 'rus', 'wal'),
  (29, '2016-06-21 18:00:00', 'c', 'pa', 'nir', 'ger'),
  (30, '2016-06-21 18:00:00', 'c', 'ma', 'ukr', 'pol'),
  (31, '2016-06-21 21:00:00', 'd', 'bo', 'cro', 'esp'),
  (32, '2016-06-21 21:00:00', 'd', 'le', 'cze', 'tur'),
  (33, '2016-06-22 18:00:00', 'f', 'sd', 'isl', 'aut'),
  (34, '2016-06-22 18:00:00', 'f', 'ly', 'hun', 'por'),
  (35, '2016-06-22 21:00:00', 'e', 'ni', 'swe', 'bel'),
  (36, '2016-06-22 21:00:00', 'e', 'li', 'ita', 'irl'),

  -- Round of 16 (eighth-finals)
  (37, '2016-06-25 15:00:00', '8', 'se', null, null),
  (38, '2016-06-25 18:00:00', '8', 'pa', null, null),
  (39, '2016-06-25 21:00:00', '8', 'le', null, null),
  (40, '2016-06-26 15:00:00', '8', 'ly', null, null),
  (41, '2016-06-26 18:00:00', '8', 'li', null, null),
  (42, '2016-06-26 21:00:00', '8', 'to', null, null),
  (43, '2016-06-27 18:00:00', '8', 'sd', null, null),
  (44, '2016-06-27 21:00:00', '8', 'ni', null, null),

  -- Quarter-finals
  (45, '2016-06-30 21:00:00', '4', 'ma', null, null),
  (46, '2016-07-01 21:00:00', '4', 'li', null, null),
  (47, '2016-07-02 21:00:00', '4', 'bo', null, null),
  (48, '2016-07-03 21:00:00', '4', 'sd', null, null),

  -- Semi-finals
  (49, '2016-07-06 21:00:00', '2', 'ly', null, null),
  (50, '2016-07-07 21:00:00', '2', 'ma', null, null),

  -- Final
  (51, '2016-07-10 21:00:00', '1', 'sd', null, null);
