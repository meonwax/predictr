'use strict';

angular.module('predictrApp')
  .controller('HomeCtrl', function($scope, Game, Shout) {
    $scope.upcomingGames = Game.upcomingGames().get();
    $scope.runningGames = Game.runningGames().get();
    $scope.shouts = Shout.query({limit: 5});
  })
  .controller('BetsCtrl', function($scope, $location, $anchorScroll, $timeout, Game, Group) {
    $scope.groups = Group.query();
    if ($location.hash()) {
      $scope.highlightedGameId = $location.hash();
      $timeout(function() {
        $anchorScroll();
      });
    }
  })
  .controller('LadderCtrl', function($scope, $http, Ladder) {
    $scope.ladder = Ladder.ladder().all();
    $scope.ladderJackpot = Ladder.ladder().jackpotOnly();
    $http.get('api/users/jackpot').then(function(response) {
      $scope.jackpot = response.data;
    });
  })
  .controller('QuestionsCtrl', function($scope, Question) {
    $scope.questions = Question.query();
  })
  .controller('RulesCtrl', function($rootScope, $scope, $http, $translate, $sce, $interpolate) {
    var currentLanguage = $translate.use();
    $http.get('values/rules-' + currentLanguage + '.md').then(function(response) {
      var html = marked(response.data);
      $scope.content = $sce.trustAsHtml($interpolate(html)($rootScope.serverInfo));
    });
  })
  .controller('ShoutboxCtrl', function($scope, Shout) {
    var query = function() {
      $scope.loading = false;
      $scope.message = null;
      $scope.shouts = Shout.query({limit: 15});
      $scope.focusInput = true;
    };
    $scope.send = function() {
      $scope.loading = true;
      $scope.focusInput = false;
      Shout.save({message: $scope.message},
        function() {
          query();
        },
        function() {
          query();
        }
      );
    };
    query();
  })
  .controller('AdminCtrl', function($scope) {
  });
