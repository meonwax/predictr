'use strict';

angular.module('predictrApp')
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
  .controller('AdminCtrl', function($scope) {
  });