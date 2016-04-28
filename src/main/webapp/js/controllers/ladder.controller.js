'use strict';

angular.module('predictrApp')
  .controller('LadderCtrl', function($rootScope, $scope, ladder, ladderJackpot, jackpot) {
    $rootScope.loading = false;
    $scope.ladder = ladder;
    $scope.ladderJackpot = ladderJackpot;
    $scope.jackpot = jackpot;
  });
