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

    $scope.send = function() {

      $scope.loading = true;

      // Prepare bets object to save
      var bets = [];
      angular.forEach($scope.bets, function(bet) {
        bets.push({
          'scoreHome': bet.scoreHome,
          'scoreAway': bet.scoreAway,
          'game': {
            'id': bet.game.id
          }
        });
      });

      // Actually save it
      Bet.save(bets,
        function() {
          toastr.success($translate.instant('bets.saveOk'));
          $scope.loading = false;
        },
        function(response) {
          var errorMessage = $translate.instant('bets.saveError') + '<br>' + response.status + ': ' + response.statusText;
          toastr.error(errorMessage);
          query();
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
