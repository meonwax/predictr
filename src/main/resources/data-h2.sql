--
-- Euro 2024 data
--
-- all timestamps in UTC
--
INSERT INTO `groups` (`id`, `priority`)
VALUES ('a', 0),
       ('b', 1),
       ('c', 2),
       ('d', 3),
       ('e', 4),
       ('f', 5),
       ('8', 6),
       ('4', 7),
       ('2', 8),
       ('1', 9);

INSERT INTO `team` (`id`, `group_id`)
VALUES ('ger', 'a'),
       ('sco', 'a'),
       ('hun', 'a'),
       ('sui', 'a'),
       ('esp', 'b'),
       ('cro', 'b'),
       ('ita', 'b'),
       ('alb', 'b'),
       ('svn', 'c'),
       ('den', 'c'),
       ('srb', 'c'),
       ('eng', 'c'),
       ('pol', 'd'),
       ('ned', 'd'),
       ('aut', 'd'),
       ('fra', 'd'),
       ('bel', 'e'),
       ('svk', 'e'),
       ('rou', 'e'),
       ('ukr', 'e'),
       ('tur', 'f'),
       ('geo', 'f'),
       ('por', 'f'),
       ('cze', 'f');

INSERT INTO `venue` (`id`, `stadium`, `city`)
VALUES (1, 'Olympiastadion Berlin', 'ber'),
       (2, 'BVB Stadion Dortmund', 'dor'),
       (3, 'Düsseldorf Arena', 'dus'),
       (4, 'Frankfurt Arena', 'fra'),
       (5, 'Arena AufSchalke', 'gel'),
       (6, 'Volksparkstadion Hamburg', 'ham'),
       (7, 'Köln Stadion', 'col'),
       (8, 'Leipzig Stadion', 'lzg'),
       (9, 'München Fußball Arena', 'mun'),
       (10, 'Stuttgart Arena', 'stu');

INSERT INTO `game` (`id`, `kickoff_time`, `group_id`, `venue_id`, `team_home_id`, `team_away_id`)
VALUES (1, '2024-06-14 19:00:00', 'a', 9, 'ger', 'sco'),

       (2, '2024-06-15 13:00:00', 'a', 7, 'hun', 'sui'),
       (3, '2024-06-15 16:00:00', 'b', 1, 'esp', 'cro'),
       (4, '2024-06-15 19:00:00', 'b', 3, 'ita', 'alb'),

       (5, '2024-06-16 13:00:00', 'd', 6, 'pol', 'ned'),
       (6, '2024-06-16 16:00:00', 'c', 10, 'svn', 'den'),
       (7, '2024-06-16 19:00:00', 'c', 5, 'srb', 'eng'),

       (8, '2024-06-17 13:00:00', 'e', 9, 'rou', 'ukr'),
       (9, '2024-06-17 16:00:00', 'e', 4, 'bel', 'svk'),
       (10, '2024-06-17 19:00:00', 'd', 3, 'aut', 'fra'),

       (11, '2024-06-18 16:00:00', 'f', 1, 'tur', 'geo'),
       (12, '2024-06-18 19:00:00', 'f', 6, 'por', 'cze'),

       (13, '2024-06-19 13:00:00', 'b', 6, 'cro', 'alb'),
       (14, '2024-06-19 16:00:00', 'a', 10, 'ger', 'hun'),
       (15, '2024-06-19 19:00:00', 'a', 7, 'sco', 'sui'),

       (16, '2024-06-20 13:00:00', 'c', 9, 'svn', 'srb'),
       (17, '2024-06-20 16:00:00', 'c', 4, 'den', 'eng'),
       (18, '2024-06-20 19:00:00', 'b', 5, 'esp', 'ita'),

       (19, '2024-06-21 13:00:00', 'e', 3, 'svk', 'ukr'),
       (20, '2024-06-21 16:00:00', 'd', 1, 'pol', 'aut'),
       (21, '2024-06-21 19:00:00', 'd', 8, 'ned', 'fra'),

       (22, '2024-06-22 13:00:00', 'f', 6, 'geo', 'cze'),
       (23, '2024-06-22 16:00:00', 'f', 2, 'tur', 'por'),
       (24, '2024-06-22 19:00:00', 'e', 7, 'bel', 'rou'),

       (25, '2024-06-23 19:00:00', 'a', 4, 'sui', 'ger'),
       (26, '2024-06-23 19:00:00', 'a', 10, 'sco', 'hun'),

       (27, '2024-06-24 19:00:00', 'b', 8, 'cro', 'ita'),
       (28, '2024-06-24 19:00:00', 'b', 3, 'alb', 'esp'),

       (29, '2024-06-25 16:00:00', 'd', 1, 'ned', 'aut'),
       (30, '2024-06-25 16:00:00', 'd', 2, 'fra', 'pol'),
       (31, '2024-06-25 19:00:00', 'c', 7, 'eng', 'svn'),
       (32, '2024-06-25 19:00:00', 'c', 9, 'den', 'srb'),

       (33, '2024-06-26 16:00:00', 'e', 4, 'svk', 'rou'),
       (34, '2024-06-26 16:00:00', 'e', 10, 'ukr', 'bel'),
       (35, '2024-06-26 19:00:00', 'f', 6, 'cze', 'tur'),
       (36, '2024-06-26 19:00:00', 'f', 5, 'geo', 'por'),

       (37, '2024-06-29 16:00:00', '8', 1, null, null),
       (38, '2024-06-29 19:00:00', '8', 2, null, null),
       (39, '2024-06-30 16:00:00', '8', 5, null, null),
       (40, '2024-06-30 19:00:00', '8', 7, null, null),
       (41, '2024-07-01 16:00:00', '8', 3, null, null),
       (42, '2024-07-01 19:00:00', '8', 4, null, null),
       (43, '2024-07-02 16:00:00', '8', 9, null, null),
       (44, '2024-07-02 19:00:00', '8', 8, null, null),

       (45, '2024-07-05 16:00:00', '4', 10, null, null),
       (46, '2024-07-05 19:00:00', '4', 6, null, null),
       (47, '2024-07-06 16:00:00', '4', 3, null, null),
       (48, '2024-07-06 19:00:00', '4', 1, null, null),

       (49, '2024-07-09 19:00:00', '2', 9, null, null),
       (50, '2024-07-10 19:00:00', '2', 2, null, null),

       (51, '2024-07-14 19:00:00', '1', 1, null, null);

--
-- Default configuration
--
INSERT INTO `config` (`id`, `title`, `owner`, `admin_email`, `show_important_message`, `points_result`,
                      `points_tendency`, `points_tendency_spread`)
VALUES (1, 'Predictr', 'John Doe', 'admin@example.com', true, 5, 2, 3);

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
INSERT INTO `user` (`password`, `name`, `email`, `role`, `wager`, `created_date`, `last_modified_date`, `avatar_id`)
VALUES ('$2a$10$v7GArGytza34uWKrr6xD.OMdnI5aKwiGIHly1oRdELQ.hg3Cp0nYS', 'Admin', 'admin@example.com', 'ROLE_ADMIN', 0,
        '1970-01-01', '1970-01-01', NULL),
       ('$2a$10$v7GArGytza34uWKrr6xD.OMdnI5aKwiGIHly1oRdELQ.hg3Cp0nYS', 'Sid Rowland', 'sid@example.com', 'ROLE_USER',
        5, '2024-01-03', '2024-01-04', NULL),
       ('$2a$10$v7GArGytza34uWKrr6xD.OMdnI5aKwiGIHly1oRdELQ.hg3Cp0nYS', 'Paula Marsh', 'paula@example.com', 'ROLE_USER',
        5, '2024-03-21', '2024-04-15', NULL),
       ('$2a$10$v7GArGytza34uWKrr6xD.OMdnI5aKwiGIHly1oRdELQ.hg3Cp0nYS', 'Johanna Silva', 'johanna@example.com',
        'ROLE_USER', 0, '2023-10-11', '2023-12-24', NULL);

INSERT INTO `shout` (`date`, `user_id`, `message`)
VALUES ('2015-07-15 22:19:15', 2, 'Nulla aliquet porttitor lacus luctus'),
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

INSERT INTO `question` (`question`, `deadline`, `points`)
VALUES ('Which team will win the championship?', '2024-06-14 19:00:00', 7),
       ('Which player will be the top goalscorer?', '2024-06-14 19:00:00', 7),
       ('Who will be voted the player of the tournament?', '2024-06-14 19:00:00', 7),
       ('Which referee will be assigned for the final?', '2024-06-14 19:00:00', 5);

INSERT INTO `bet` (`user_id`, `game_id`, `score_home`, `score_away`)
VALUES (1, 1, 1, 2),
       (1, 2, 0, 1),
       (1, 3, 3, 0),
       (2, 1, 0, 0),
       (2, 2, 3, 2),
       (2, 5, 1, 2),
       (2, 14, 3, 1);

INSERT INTO `answer` (`user_id`, `question_id`, `answer`)
VALUES (1, 1, 'Germany'),
       (1, 4, 'Jonas Eriksson'),
       (3, 1, 'England'),
       (3, 4, 'Felix Brych');
