'use strict';

angular.module('predictrApp')
  .controller('AdminCtrl', function($rootScope, $scope, toastr, $translate, Game, games, teams, Question, questions, users) {
    $rootScope.loading = false;
    $scope.games = games;
    $scope.teams = teams;
    $scope.questions = questions;
    $scope.users = users;
    $scope.hasStarted = Game.hasStarted;

    var isInteger = function(str) {
      var n = ~~Number(str);
      return String(n) == str && n >= 0;
    };

    $scope.saveGames = function() {
      $scope.gamesSaving = true;

      // Prepare DTO array to save
      var dtos = [];
      angular.forEach($scope.games, function(game) {
          dtos.push({
            'id': game.id,
            'teamHome': game.teamHome && game.teamHome.id ? game.teamHome : null,
            'teamAway': game.teamAway && game.teamAway.id ? game.teamAway : null,
            'scoreHome': !game.scoreHome && game.scoreHome != '0' ? null : game.scoreHome,
            'scoreAway': !game.scoreAway && game.scoreAway != '0' ? null : game.scoreAway,
            'notes': game.notes
          });
      });

      // Actually save it
      Game.all().save(dtos,
        function() {
          toastr.success($translate.instant('admin.gamesSaveOk'));
          $scope.gamesSaving = false;
        },
        function(response) {
          var errorMessage = $translate.instant('admin.gamesSaveError') + '<br>' + response.status + ': ' + response.statusText;
          toastr.error(errorMessage);
          $scope.gamesSaving = false;
        }
      );
    };

    $scope.saveQuestions = function() {
      $scope.questionsSaving = true;

      // Prepare DTO array to save
      var dtos = [];
      angular.forEach($scope.questions, function(question) {
        // Check mandatory fields
        if(question.question && question.deadline && !isNaN(question.points)) {
          dtos.push({
            'id': question.id,
            'question': question.question,
            'deadline': question.deadline,
            'points': question.points,
            'correctAnswer': question.correctAnswer
          });
        }
      });

      // Actually save it
      Question.all().save(dtos,
        function() {
          toastr.success($translate.instant('admin.questionsSaveOk'));
          $scope.questionsSaving = false;
        },
        function(response) {
          var errorMessage = $translate.instant('admin.questionsSaveError') + '<br>' + response.status + ': ' + response.statusText;
          toastr.error(errorMessage);
          $scope.questionsSaving = false;
        }
      );
    };
  });
