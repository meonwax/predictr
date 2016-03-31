--
-- Euro 2016 data
--
INSERT INTO `groups` (`id`) VALUES ('a'), ('b'), ('c'), ('d'), ('e'), ('f'), ('8'), ('4'), ('2'), ('1');

INSERT INTO `team` (`id`, `group_id`) VALUES
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

INSERT INTO `locations` (`id`, `stadium`, `city`) VALUES
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

INSERT INTO `game` (`kickoff_time`, `group_id`, `location_id`, `team_home_id`, `team_away_id`) VALUES
  -- Matchday 1
  ('2016-06-10 21:00:00', 'a', 'sd', 'fra', 'rou'),
  ('2016-06-11 15:00:00', 'a', 'le', 'alb', 'sui'),
  ('2016-06-11 18:00:00', 'b', 'bo', 'wal', 'svk'),
  ('2016-06-11 21:00:00', 'b', 'ma', 'eng', 'rus'),
  ('2016-06-12 15:00:00', 'd', 'pa', 'tur', 'cro'),
  ('2016-06-12 18:00:00', 'c', 'ni', 'pol', 'nir'),
  ('2016-06-12 21:00:00', 'c', 'li', 'ger', 'ukr'),
  ('2016-06-13 15:00:00', 'd', 'to', 'esp', 'cze'),
  ('2016-06-13 18:00:00', 'e', 'sd', 'irl', 'swe'),
  ('2016-06-13 21:00:00', 'e', 'ly', 'bel', 'ita'),
  ('2016-06-14 18:00:00', 'f', 'bo', 'aut', 'hun'),
  ('2016-06-14 21:00:00', 'f', 'se', 'por', 'isl'),

  -- Matchday 2
  ('2016-06-15 15:00:00', 'b', 'li', 'rus', 'svk'),
  ('2016-06-15 18:00:00', 'a', 'pa', 'rou', 'sui'),
  ('2016-06-15 21:00:00', 'a', 'ma', 'fra', 'alb'),
  ('2016-06-16 15:00:00', 'b', 'le', 'eng', 'wal'),
  ('2016-06-16 18:00:00', 'c', 'ly', 'ukr', 'nir'),
  ('2016-06-16 21:00:00', 'c', 'sd', 'ger', 'pol'),
  ('2016-06-17 15:00:00', 'e', 'to', 'ita', 'swe'),
  ('2016-06-17 18:00:00', 'd', 'se', 'cze', 'cro'),
  ('2016-06-17 21:00:00', 'd', 'ni', 'esp', 'tur'),
  ('2016-06-18 15:00:00', 'e', 'bo', 'bel', 'irl'),
  ('2016-06-18 18:00:00', 'f', 'ma', 'isl', 'hun'),
  ('2016-06-18 21:00:00', 'f', 'pa', 'por', 'aut'),

  -- Matchday 3
  ('2016-06-19 21:00:00', 'a', 'li', 'sui', 'fra'),
  ('2016-06-19 21:00:00', 'a', 'ly', 'rou', 'alb'),
  ('2016-06-20 21:00:00', 'b', 'se', 'svk', 'eng'),
  ('2016-06-20 21:00:00', 'b', 'to', 'rus', 'wal'),
  ('2016-06-21 18:00:00', 'c', 'pa', 'nir', 'ger'),
  ('2016-06-21 18:00:00', 'c', 'ma', 'ukr', 'pol'),
  ('2016-06-21 21:00:00', 'd', 'bo', 'cro', 'esp'),
  ('2016-06-21 21:00:00', 'd', 'le', 'cze', 'tur'),
  ('2016-06-22 18:00:00', 'f', 'sd', 'isl', 'aut'),
  ('2016-06-22 18:00:00', 'f', 'ly', 'hun', 'por'),
  ('2016-06-22 21:00:00', 'e', 'ni', 'swe', 'bel'),
  ('2016-06-22 21:00:00', 'e', 'li', 'ita', 'irl'),

  -- Round of 16 (eighth-finals)
  ('2016-06-25 15:00:00', '8', 'se', null, null),
  ('2016-06-25 18:00:00', '8', 'pa', null, null),
  ('2016-06-25 21:00:00', '8', 'le', null, null),
  ('2016-06-26 15:00:00', '8', 'ly', null, null),
  ('2016-06-26 18:00:00', '8', 'li', null, null),
  ('2016-06-26 21:00:00', '8', 'to', null, null),
  ('2016-06-27 18:00:00', '8', 'sd', null, null),
  ('2016-06-27 21:00:00', '8', 'ni', null, null),

  -- Quarter-finals
  ('2016-06-30 21:00:00', '4', 'ma', null, null),
  ('2016-07-01 21:00:00', '4', 'li', null, null),
  ('2016-07-02 21:00:00', '4', 'bo', null, null),
  ('2016-07-03 21:00:00', '4', 'sd', null, null),

  -- Semi-finals
  ('2016-07-06 21:00:00', '2', 'ly', null, null),
  ('2016-07-07 21:00:00', '2', 'ma', null, null),

  -- Final
  ('2016-07-10 21:00:00', '1', 'sd', null, null);


--
-- Dummy data for development
--
INSERT INTO `user` (`password`, `name`, `email`, `is_admin`, `wager`, `created_date`, `last_modified_date`) VALUES
    ('aaa', 'Admin', 'admin@example.com', '1', 0, '2015-02-01', '2015-02-01'),
    ('bbb', 'Sid Rowland', 'sid@example.com', '0', 5, '2015-02-01', '2015-02-01'),
    ('ccc', 'Paula Marsh', 'paula@example.com', '0', 5, '2015-02-01', '2015-02-01'),
    ('ddd', 'Johanna Silva', 'johanna@example.com', '0', 0, '2015-02-01', '2015-02-01');

INSERT INTO `shout` (`date`, `user_id`, `message`) VALUES
  ('2015-07-15 22:19:15', 2, 'Nulla aliquet porttitor lacus luctus'),
  ('2015-07-15 14:34:46', 4, 'Semper feugiat nibh sed pulvinar proin gravida hendrerit lectus'),
  ('2015-07-15 12:19:10', 3, 'Fermentum odio eu feugiat pretium nibh ipsum consequat'),
  ('2015-07-15 12:18:44', 3, 'Convallis a cras semper'),
  ('2015-07-14 17:40:52', 3, 'Yes'),
  ('2015-07-14 09:33:06', 1, 'Orci sagittis eu volutpat odio facilisis mauris sit amet :)'),
  ('2015-07-14 01:22:40', 3, 'Dolor sed viverra ipsum.'),
  ('2015-06-17 22:35:59', 2, 'Blandit volutpat maecenas volutpat blandit aliquam etiam erat'),
  ('2015-05-26 22:28:52', 4, 'Vitae suscipit tellus mauris a diam maecenas sed enim'),
  ('2014-07-15 22:19:15', 2, 'Nulla aliquet porttitor lacus luctus'),
  ('2014-07-15 14:34:46', 4, 'Semper feugiat nibh sed pulvinar proin gravida hendrerit lectus'),
  ('2014-07-15 12:19:10', 3, 'Fermentum odio eu feugiat pretium nibh ipsum consequat'),
  ('2014-07-15 12:18:44', 3, 'Convallis a cras semper'),
  ('2014-07-14 17:40:52', 3, 'Yes'),
  ('2014-07-14 09:33:06', 1, 'Orci sagittis eu volutpat odio facilisis mauris sit amet :)'),
  ('2014-07-14 01:22:40', 3, 'Dolor sed viverra ipsum.'),
  ('2014-06-17 22:35:59', 2, 'Blandit volutpat maecenas volutpat blandit aliquam etiam erat'),
  ('2014-05-26 22:28:52', 4, 'Vitae suscipit tellus mauris a diam maecenas sed enim');

INSERT INTO `question` (`question`, `deadline`, `points`) VALUES
  ('Which team will win the championship?', '2016-06-10 19:00:00', 7),
  ('Which player will be the top goalscorer?', '2016-06-10 19:00:00', 7),
  ('Who will be voted the player of the tournament?', '2016-06-10 19:00:00', 7),
  ('Which referee will be assigned for the final?', '2016-06-25 13:00:00', 5);

INSERT INTO `bet` (`score_away`, `score_home`, `game_id`, `user_id`) VALUES
  (1, 2, 1, 1),
  (0, 1, 2, 1),
  (3, 0, 3, 1),
  (5, 5, 2, 2);
