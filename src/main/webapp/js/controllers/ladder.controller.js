'use strict';

angular.module('predictrApp')
  .controller('LadderCtrl', function($rootScope, $scope, ladder, ladderJackpot, jackpot, progress) {
    $rootScope.loading = false;
    $scope.ladder = ladder;
    $scope.ladderJackpot = ladderJackpot;
    $scope.jackpot = jackpot;
    $scope.progress = progress;
  });
