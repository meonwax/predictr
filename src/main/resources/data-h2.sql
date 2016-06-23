--
-- Euro 2016 data
--
INSERT INTO `groups` (`id`, `priority`) VALUES
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

INSERT INTO `game` (`id`, `kickoff_time`, `score_away`, `score_home`, `group_id`, `location_id`, `team_away_id`, `team_home_id`) VALUES
  -- Matchday 1
  (1, '2016-06-10 21:00:00', 1, 2, 'a', 'sd', 'rou', 'fra'),
  (2, '2016-06-11 15:00:00', 1, 0, 'a', 'le', 'sui', 'alb'),
  (3, '2016-06-11 18:00:00', 1, 2, 'b', 'bo', 'svk', 'wal'),
  (4, '2016-06-11 21:00:00', 1, 1, 'b', 'ma', 'rus', 'eng'),
  (5, '2016-06-12 15:00:00', 1, 0, 'd', 'pa', 'cro', 'tur'),
  (6, '2016-06-12 18:00:00', 0, 1, 'c', 'ni', 'nir', 'pol'),
  (7, '2016-06-12 21:00:00', 0, 2, 'c', 'li', 'ukr', 'ger'),
  (8, '2016-06-13 15:00:00', 0, 1, 'd', 'to', 'cze', 'esp'),
  (9, '2016-06-13 18:00:00', 1, 1, 'e', 'sd', 'swe', 'irl'),
  (10, '2016-06-13 21:00:00', 2, 0, 'e', 'ly', 'ita', 'bel'),
  (11, '2016-06-14 18:00:00', 2, 0, 'f', 'bo', 'hun', 'aut'),
  (12, '2016-06-14 21:00:00', 1, 1, 'f', 'se', 'isl', 'por'),

  -- Matchday 2
  (13, '2016-06-15 15:00:00', 2, 1, 'b', 'li', 'svk', 'rus'),
  (14, '2016-06-15 18:00:00', 1, 1, 'a', 'pa', 'sui', 'rou'),
  (15, '2016-06-15 21:00:00', 0, 2, 'a', 'ma', 'alb', 'fra'),
  (16, '2016-06-16 15:00:00', 1, 2, 'b', 'le', 'wal', 'eng'),
  (17, '2016-06-16 18:00:00', 2, 0, 'c', 'ly', 'nir', 'ukr'),
  (18, '2016-06-16 21:00:00', 0, 0, 'c', 'sd', 'pol', 'ger'),
  (19, '2016-06-17 15:00:00', 0, 1, 'e', 'to', 'swe', 'ita'),
  (20, '2016-06-17 18:00:00', 2, 2, 'd', 'se', 'cro', 'cze'),
  (21, '2016-06-17 21:00:00', 0, 3, 'd', 'ni', 'tur', 'esp'),
  (22, '2016-06-18 15:00:00', 0, 3, 'e', 'bo', 'irl', 'bel'),
  (23, '2016-06-18 18:00:00', 1, 1, 'f', 'ma', 'hun', 'isl'),
  (24, '2016-06-18 21:00:00', 0, 0, 'f', 'pa', 'aut', 'por'),

  -- Matchday 3
  (25, '2016-06-19 21:00:00', 0, 0, 'a', 'li', 'fra', 'sui'),
  (26, '2016-06-19 21:00:00', 1, 0, 'a', 'ly', 'alb', 'rou'),
  (27, '2016-06-20 21:00:00', 0, 0, 'b', 'se', 'eng', 'svk'),
  (28, '2016-06-20 21:00:00', 3, 0, 'b', 'to', 'wal', 'rus'),
  (29, '2016-06-21 18:00:00', null, null, 'c', 'pa', 'ger', 'nir'),
  (30, '2016-06-21 18:00:00', null, null, 'c', 'ma', 'pol', 'ukr'),
  (31, '2016-06-21 21:00:00', null, null, 'd', 'bo', 'esp', 'cro'),
  (32, '2016-06-21 21:00:00', null, null, 'd', 'le', 'tur', 'cze'),
  (33, '2016-06-22 18:00:00', null, null, 'f', 'sd', 'aut', 'isl'),
  (34, '2016-06-22 18:00:00', null, null, 'f', 'ly', 'por', 'hun'),
  (35, '2016-06-22 21:00:00', null, null, 'e', 'ni', 'bel', 'swe'),
  (36, '2016-06-22 21:00:00', null, null, 'e', 'li', 'irl', 'ita'),

  -- Round of 16 (eighth-finals)
  (37, '2016-06-25 15:00:00', null, null, '8', 'se', null, null),
  (38, '2016-06-25 18:00:00', null, null, '8', 'pa', null, null),
  (39, '2016-06-25 21:00:00', null, null, '8', 'le', null, null),
  (40, '2016-06-26 15:00:00', null, null, '8', 'ly', null, null),
  (41, '2016-06-26 18:00:00', null, null, '8', 'li', null, null),
  (42, '2016-06-26 21:00:00', null, null, '8', 'to', null, null),
  (43, '2016-06-27 18:00:00', null, null, '8', 'sd', null, null),
  (44, '2016-06-27 21:00:00', null, null, '8', 'ni', null, null),

  -- Quarter-finals
  (45, '2016-06-30 21:00:00', null, null, '4', 'ma', null, null),
  (46, '2016-07-01 21:00:00', null, null, '4', 'li', null, null),
  (47, '2016-07-02 21:00:00', null, null, '4', 'bo', null, null),
  (48, '2016-07-03 21:00:00', null, null, '4', 'sd', null, null),

  -- Semi-finals
  (49, '2016-07-06 21:00:00', null, null, '2', 'ly', null, null),
  (50, '2016-07-07 21:00:00', null, null, '2', 'ma', null, null),

  -- Final
  (51, '2016-07-10 21:00:00', null, null, '1', 'sd', null, null);


--
-- Dummy data for development
--

-- Password: 123vorbei
INSERT INTO `user` (`password`, `name`, `email`, `role`, `wager`, `created_date`, `last_modified_date`, `avatar_id`) VALUES
  ('$2a$10$v7GArGytza34uWKrr6xD.OMdnI5aKwiGIHly1oRdELQ.hg3Cp0nYS', 'Admin', 'admin@example.com', 'ROLE_ADMIN', 0, '2015-02-01', '2015-02-01', NULL),
  ('$2a$10$v7GArGytza34uWKrr6xD.OMdnI5aKwiGIHly1oRdELQ.hg3Cp0nYS', 'Sid Rowland', 'sid@example.com', 'ROLE_USER', 5, '2016-01-03', '2016-01-05', NULL),
  ('$2a$10$v7GArGytza34uWKrr6xD.OMdnI5aKwiGIHly1oRdELQ.hg3Cp0nYS', 'Paula Marsh', 'paula@example.com', 'ROLE_USER', 5, '2016-03-21', '2016-04-01', NULL),
  ('$2a$10$v7GArGytza34uWKrr6xD.OMdnI5aKwiGIHly1oRdELQ.hg3Cp0nYS', 'Johanna Silva', 'johanna@example.com', 'ROLE_USER', 0, '2015-10-11', '2015-12-24', NULL);

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

INSERT INTO `bet` (`user_id`, `game_id`, `score_home`, `score_away` ) VALUES
  (1, 1, 1, 2),
  (1, 2, 0, 1),
  (1, 3, 3, 0),
  (2, 1, 0, 0),
  (2, 2, 3, 2),
  (2, 5, 1, 2),
  (2, 14, 3, 1);

INSERT INTO `answer` (`user_id`, `question_id`, `answer` ) VALUES
  (1, 1, 'Germany'),
  (1, 4, 'Jonas Eriksson'),
  (3, 1, 'England'),
  (3, 4, 'Felix Brych');
