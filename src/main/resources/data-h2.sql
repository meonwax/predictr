--
-- World Cup 2018 data
--
-- all timestamps in UTC
--
INSERT INTO `groups` (`id`, `priority`) VALUES
  ('a', 0),
  ('b', 1),
  ('c', 2),
  ('d', 3),
  ('e', 4),
  ('f', 5),
  ('g', 6),
  ('h', 7),
  ('8', 8),
  ('4', 9),
  ('2', 10),
  ('3', 11),
  ('1', 12);

INSERT INTO `team` (`id`, `group_id`) VALUES
  ('rus', 'a'),
  ('ksa', 'a'),
  ('egy', 'a'),
  ('uru', 'a'),
  ('por', 'b'),
  ('esp', 'b'),
  ('mar', 'b'),
  ('irn', 'b'),
  ('fra', 'c'),
  ('aus', 'c'),
  ('per', 'c'),
  ('den', 'c'),
  ('arg', 'd'),
  ('isl', 'd'),
  ('cro', 'd'),
  ('nga', 'd'),
  ('bra', 'e'),
  ('sui', 'e'),
  ('crc', 'e'),
  ('srb', 'e'),
  ('ger', 'f'),
  ('mex', 'f'),
  ('swe', 'f'),
  ('kor', 'f'),
  ('bel', 'g'),
  ('pan', 'g'),
  ('tun', 'g'),
  ('eng', 'g'),
  ('pol', 'h'),
  ('sen', 'h'),
  ('col', 'h'),
  ('jpn', 'h');

INSERT INTO `venue` (`id`, `stadium`, `city`) VALUES
  (1, 'Luzhniki Stadium', 'mow'),
  (2, 'Otkrytiye Arena', 'mow'),
  (3, 'Krestovsky Stadium', 'led'),
  (4, 'Kaliningrad Stadium', 'kgd'),
  (5, 'Kazan Arena', 'kzn'),
  (6, 'Nizhny Novgorod Stadium', 'goj'),
  (7, 'Cosmos Arena', 'kuf'),
  (8, 'Volgograd Arena', 'vog'),
  (9, 'Mordovia Arena', 'skx'),
  (10, 'Rostov Arena', 'rvi'),
  (11, 'Fisht Olympic Stadium', 'aer'),
  (12, 'Central Stadium', 'svx');

INSERT INTO `game` (`id`, `kickoff_time`, `group_id`, `venue_id`, `team_home_id`, `team_away_id`) VALUES
  (1, '2018-06-14 15:00:00', 'a', 1, 'rus', 'ksa'),
  (2, '2018-06-15 12:00:00', 'a', 12, 'egy', 'uru'),
  (17, '2018-06-19 18:00:00', 'a', 3, 'rus', 'egy'),
  (18, '2018-06-20 15:00:00', 'a', 10, 'uru', 'ksa'),
  (33, '2018-06-25 14:00:00', 'a', 7, 'uru', 'rus'),
  (34, '2018-06-25 14:00:00', 'a', 8, 'ksa', 'egy'),

  (3, '2018-06-15 18:00:00', 'b', 11, 'por', 'esp'),
  (4, '2018-06-15 15:00:00', 'b', 3, 'mar', 'irn'),
  (19, '2018-06-20 12:00:00', 'b', 1, 'por', 'mar'),
  (20, '2018-06-20 18:00:00', 'b', 5, 'irn', 'esp'),
  (35, '2018-06-25 18:00:00', 'b', 9, 'irn', 'por'),
  (36, '2018-06-25 18:00:00', 'b', 4, 'esp', 'mar'),

  (5, '2018-06-16 10:00:00', 'c', 5, 'fra', 'aus'),
  (6, '2018-06-16 16:00:00', 'c', 9, 'per', 'den'),
  (21, '2018-06-21 15:00:00', 'c', 12, 'fra', 'per'),
  (22, '2018-06-21 12:00:00', 'c', 7, 'den', 'aus'),
  (37, '2018-06-26 14:00:00', 'c', 1, 'den', 'fra'),
  (38, '2018-06-26 15:00:00', 'c', 11, 'aus', 'per'),

  (7, '2018-06-16 13:00:00', 'd', 2, 'arg', 'isl'),
  (8, '2018-06-16 19:00:00', 'd', 4, 'cro', 'nga'),
  (23, '2018-06-21 18:00:00', 'd', 6, 'arg', 'cro'),
  (24, '2018-06-22 15:00:00', 'd', 8, 'nga', 'isl'),
  (39, '2018-06-26 18:00:00', 'd', 3, 'nga', 'arg'),
  (40, '2018-06-26 18:00:00', 'd', 10, 'isl', 'cro'),

  (9, '2018-06-17 18:00:00', 'e', 10, 'bra', 'sui'),
  (10, '2018-06-17 12:00:00', 'e', 7, 'crc', 'srb'),
  (25, '2018-06-22 12:00:00', 'e', 3, 'bra', 'crc'),
  (26, '2018-06-22 18:00:00', 'e', 4, 'srb', 'sui'),
  (41, '2018-06-27 18:00:00', 'e', 2, 'srb', 'bra'),
  (42, '2018-06-27 18:00:00', 'e', 6, 'sui', 'crc'),

  (11, '2018-06-17 15:00:00', 'f', 1, 'ger', 'mex'),
  (12, '2018-06-18 12:00:00', 'f', 6, 'swe', 'kor'),
  (27, '2018-06-23 18:00:00', 'f', 11, 'ger', 'swe'),
  (28, '2018-06-23 15:00:00', 'f', 10, 'kor', 'mex'),
  (43, '2018-06-27 14:00:00', 'f', 5, 'kor', 'ger'),
  (44, '2018-06-27 14:00:00', 'f', 12, 'mex', 'swe'),

  (13, '2018-06-18 15:00:00', 'g', 11, 'bel', 'pan'),
  (14, '2018-06-18 18:00:00', 'g', 8, 'tun', 'eng'),
  (29, '2018-06-23 12:00:00', 'g', 2, 'bel', 'tun'),
  (30, '2018-06-24 12:00:00', 'g', 6, 'eng', 'pan'),
  (45, '2018-06-28 18:00:00', 'g', 4, 'eng', 'bel'),
  (46, '2018-06-28 18:00:00', 'g', 9, 'pan', 'tun'),

  (15, '2018-06-19 15:00:00', 'h', 2, 'pol', 'sen'),
  (16, '2018-06-19 12:00:00', 'h', 9, 'col', 'jpn'),
  (31, '2018-06-24 15:00:00', 'h', 5, 'pol', 'col'),
  (32, '2018-06-24 18:00:00', 'h', 12, 'jpn', 'sen'),
  (47, '2018-06-28 14:00:00', 'h', 8, 'jpn', 'pol'),
  (48, '2018-06-28 14:00:00', 'h', 7, 'sen', 'col'),

  (49, '2018-06-30 14:00:00', '8', 11, null, null),
  (50, '2018-06-30 18:00:00', '8', 5, null, null),
  (51, '2018-07-01 14:00:00', '8', 1, null, null),
  (52, '2018-07-01 18:00:00', '8', 6, null, null),
  (53, '2018-07-02 14:00:00', '8', 7, null, null),
  (54, '2018-07-02 18:00:00', '8', 10, null, null),
  (55, '2018-07-03 14:00:00', '8', 3, null, null),
  (56, '2018-07-03 18:00:00', '8', 2, null, null),

  (57, '2018-07-06 14:00:00', '4', 6, null, null),
  (58, '2018-07-06 18:00:00', '4', 5, null, null),
  (59, '2018-07-07 18:00:00', '4', 11, null, null),
  (60, '2018-07-07 14:00:00', '4', 7, null, null),

  (61, '2018-07-10 18:00:00', '2', 3, null, null),
  (62, '2018-07-11 18:00:00', '2', 1, null, null),

  (63, '2018-07-14 14:00:00', '3', 3, null, null),

  (64, '2018-07-15 15:00:00', '1', 1, null, null);

--
-- Default configuration
--
INSERT INTO `config` (`id`, `title`, `owner`, `admin_email`, `show_important_message`, `points_result`, `points_tendency`, `points_tendency_spread`) VALUES
  (1, 'Predictr', 'John Doe', 'admin@example.com', true, 5, 2, 3);

UPDATE `config` SET
  `rules_de` =
'### Für das Tippspiel gelten folgende Regeln

 - Es wird immer das Ergebnis nach 90 Minuten (Gruppenspiele) bzw. das Ergebnis nach eventueller Verlängerung (Finalspiele) getippt.
 Ein mögliches Elfmeterschießen ist für die Tippabgabe nicht relevant.

 - Die Punkte werden wie folgt vergeben:
   - **Richtiges Ergebnis: {{pointsResult}} Punkte**
   - **Richtige Tordifferenz bei richtiger Tendenz: {{pointsTendencySpread}} Punkte**
   - **Richtige Tendenz: {{pointsTendency}} Punkte**


 - Die erreichbaren Punkte für die Spezialfragen sind jeweils angegeben.
 Wer am Ende des Turniers die meisten Punkte erreicht hat, gewinnt das Tippspiel. Tipper mit gleicher Punktzahl teilen sich den entsprechenden Ranglistenplatz.

 - Jeder Tipp muss vor Anpfiff eines jeweiligen Spiels abgegeben werden und ist bis dahin beliebig oft änderbar.
 Die Anstoßzeiten sind im Spielplan angegeben.
 Nach Anpfiff ist die Tippabgabe für dieses Spiel gesperrt.

 - **Die Antworten auf die Spezialfragen müssen vor Ablauf der Deadline (Zeitpunkt in der Tabelle angegeben) abgegeben werden.**
 Danach ist die Antwortabgabe gesperrt. Bitte achtet auf die richtige Schreibweise.

 - Maßgeblich ist die unten angegebene Serverzeit.
 Alle Zeiten sind in Mitteleuropäischer Sommerzeit (MESZ) angegeben.

 - Eine Punktevergabe erfolgt, sobald das offizielle Ergebnis des Spiels in die Datenbank eingetragen wurde.
 Dies geschieht möglichst zeitnah, kleinere Verzögerungen sind jedoch nicht auszuschließen.

 - Bei einem festen Einsatz von **5 €** kann um den **Jackpot** mitgespielt werden.
 In einer separaten Rangliste werden die Spieler gelistet, die **vor Beginn** des Turniers 5 € in den Jackpot eingezahlt haben.
 Der Sieger der Jackpot-Rangliste erhält den kompletten Jackpot. Bei gleicher Punktzahl wird der Gewinn entsprechend aufgeteilt.
 Der Einsatz muss bis zum Beginn des Turniers per Überweisung oder persönlich hinterlegt werden.
 Für die Teilnahme am Jackpotspiel bitte eine E-Mail an <a href="mailto:{{adminEmail}}">{{adminEmail}}</a> senden.

 - **Das letzte Wort hat der Betreiber des Tippspiels.**

 Fragen oder Unklarheiten bitte in der Shoutbox ansprechen. Ebenso auftretende Programmfehler.

 Viel Spaß beim Tippen und Mitfiebern wünscht Euch

 {{owner}}',
   `rules_en` =
'### Rules for the prediction game

- Always bet on the match result after 90 minutes (group matches) or on the result after extra time (finals).
A potential penalty shootout will be ignored.

- How many points do I get?
  - **Correct result: {{pointsResult}} points**
  - **Correct goal difference with correct trend: {{pointsTendencySpread}} points**
  - **Correct Trend: {{pointsTendency}} points**


- Points for additional questions: See the respective question.
To win the prediction game you need to have the most points at the end of the tournament. Multiple players with identical score will share the respective ranking position.

- Each guess must be placed before kick-off of the respective match. You may change your guesses until this deadline.
For match dates and times see the integrated schedule.
After kickoff, your guess for the relevant match will be locked.

- **Deadlines for additional questions: See date and time specified with each question**
After this deadline, your guess will be locked. Please ensure a correct spelling to avoid invalid guesses.

- Reference time is this server''s time specified below.
All time indications refer to Central European Summer Time (CEST).

- Score calculation executes when the official final score of a match has been entered into the database.
This will be done as soon as possible but minor delays may occur.

- With a fixed wager of **5 €** you can play for the **jackpot**.
Jackpot players are listed in a separate ranking.
The winner of the jackpot ranking receives the complete jackpot. Multiple players with identical maximum score will share the jackpot.
The wager must be payed **before tournament starts** by bank transfer or personal deposit.
For your jackpot bet participation send an email to <a href="mailto:{{adminEmail}}">{{adminEmail}}</a>.

- **The operator of this game will have the last word in any dispute.**

Please contact us via shoutbox if you have any questions or find bugs.

Happy betting!

{{owner}}'
  WHERE `id` = 1;

--
-- Dummy data for development
--

-- Password: 123vorbei
INSERT INTO `user` (`password`, `name`, `email`, `role`, `wager`, `created_date`, `last_modified_date`, `avatar_id`) VALUES
  ('$2a$10$v7GArGytza34uWKrr6xD.OMdnI5aKwiGIHly1oRdELQ.hg3Cp0nYS', 'Admin', 'admin@example.com', 'ROLE_ADMIN', 0, '2016-02-01', '2016-02-01', NULL),
  ('$2a$10$v7GArGytza34uWKrr6xD.OMdnI5aKwiGIHly1oRdELQ.hg3Cp0nYS', 'Sid Rowland', 'sid@example.com', 'ROLE_USER', 5, '2018-01-03', '2018-01-05', NULL),
  ('$2a$10$v7GArGytza34uWKrr6xD.OMdnI5aKwiGIHly1oRdELQ.hg3Cp0nYS', 'Paula Marsh', 'paula@example.com', 'ROLE_USER', 5, '2018-03-21', '2018-04-01', NULL),
  ('$2a$10$v7GArGytza34uWKrr6xD.OMdnI5aKwiGIHly1oRdELQ.hg3Cp0nYS', 'Johanna Silva', 'johanna@example.com', 'ROLE_USER', 0, '2017-10-11', '2017-12-24', NULL);

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
  ('2014-07-14 17:40:52', 3, 'Nope'),
  ('2014-07-14 09:33:06', 1, 'Orci sagittis eu volutpat odio facilisis mauris sit amet :)'),
  ('2014-07-14 01:22:40', 3, 'Dolor sed viverra ipsum.'),
  ('2014-06-17 22:35:59', 2, 'Blandit volutpat maecenas volutpat blandit aliquam etiam erat'),
  ('2014-05-26 22:28:52', 4, 'Vitae suscipit tellus mauris a diam maecenas sed enim');

INSERT INTO `question` (`question`, `deadline`, `points`) VALUES
  ('Which team will win the championship?', '2018-06-14 17:00:00', 7),
  ('Which player will be the top goalscorer?', '2018-06-14 17:00:00', 7),
  ('Who will be voted the player of the tournament?', '2018-06-14 17:00:00', 7),
  ('Which referee will be assigned for the final?', '2018-06-30 16:00:00', 5);

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
