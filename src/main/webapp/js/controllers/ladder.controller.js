'use strict';

angular.module('predictrApp')
  .controller('LadderCtrl', function($scope, ladder, ladderJackpot, jackpot) {
    $scope.ladder = ladder;
    $scope.ladderJackpot = ladderJackpot;
    $scope.jackpot = jackpot;
  });
