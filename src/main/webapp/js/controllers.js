'use strict';

angular.module('predictrApp')
  .controller('HomeCtrl', function($scope, Game, Shout) {
    $scope.upcomingGames = Game.upcomingGames().get();
    $scope.runningGames = Game.runningGames().get();
    $scope.shouts = Shout.query();
  })
  .controller('BetsCtrl', function($scope, $location, $anchorScroll, $timeout, Game, Group) {
    $scope.groups = Group.query();
    if($location.hash()) {
      $scope.highlightedGameId = $location.hash();
      $timeout(function() {
        console.log($location.hash());
        $anchorScroll();
      });
    }
  })
  .controller('LadderCtrl', function($scope, $http, Ladder) {
    $scope.ladder = Ladder.ladder().all();
    $scope.ladderJackpot = Ladder.ladder().jackpotOnly();
    $http.get('/api/users/jackpot').then(function(response) {
      $scope.jackpot = response.data;
    });
  })
  .controller('QuestionsCtrl', function($scope, Question) {
    $scope.questions = Question.query();
  })
  .controller('RulesCtrl', function($scope) {
  })
  .controller('ShoutboxCtrl', function($scope) {
  })
  .controller('AdminCtrl', function($scope) {
  });
