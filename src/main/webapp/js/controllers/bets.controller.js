'use strict';

angular.module('predictrApp')
  .controller('BetsCtrl', function($scope, $location, $anchorScroll, $timeout, $translate, toastr, Account, Group, Bet) {
    var query = function() {
      $scope.loading = false;
      $scope.groups = Group.query();
      Account.get(function(account) {
        // Reindex bets using gameId
        $scope.bets = {};
        angular.forEach(account.bets, function(bet) {
          $scope.bets[bet.game.id] = bet;
        });
      });
    };
    $scope.send = function(form) {
      $scope.loading = true;
      Bet.save($scope.groups,
        function() {
          toastr.success($translate.instant('bets.saveOk'));
          query();
        },
        function(response) {
          var errorMessage = $translate.instant('bets.saveError') + '<br>' + response.status + ': ' + response.statusText;
          toastr.error(errorMessage);
          $scope.loading = false;
        }
      );
    };
    query();
    if ($location.hash()) {
      $scope.highlightedGameId = $location.hash();
      $timeout(function() {
        $anchorScroll();
      });
    }
  });
