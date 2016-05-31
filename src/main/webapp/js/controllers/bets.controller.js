'use strict';

angular.module('predictrApp')
  .controller('BetsCtrl', function($rootScope, $scope, $location, $anchorScroll, $timeout, $translate, toastr, $uibModal, Game, Bet, groups) {

    $scope.groups = groups;
    $rootScope.loading = false;

    if ($location.hash()) {
      $scope.highlightedGameId = $location.hash();
      $timeout(function() {
        $anchorScroll();
      });
    }

    $scope.send = function() {
      $scope.saving = true;

      // Prepare DTO array to save
      var bets = [];
      angular.forEach($scope.groups, function(group) {
        angular.forEach(group.games, function(game) {
          if(game.bets[0]) {
            bets.push({
              'scoreHome': game.bets[0].scoreHome,
              'scoreAway': game.bets[0].scoreAway,
              'game': {
                'id': game.id
              }
            });
          }
        });
      });

      // Actually save it
      Bet.save(bets,
        function() {
          toastr.success($translate.instant('bets.saveOk'));
          $scope.saving = false;
        },
        function(response) {
          var errorMessage = $translate.instant('bets.saveError') + '<br>' + response.status + ': ' + response.statusText;
          toastr.error(errorMessage);
          $scope.saving = false;
        }
      );
    };

    $scope.showOther = function(game) {

      // Inline modal controller function
      var otherBetsCtrl = function($scope, $uibModalInstance) {
        $scope.game = game
        $scope.hasStarted = Game.hasStarted(game);
        if($scope.hasStarted) {
          Bet.query({gameId: game.id}, function(result) {
            $scope.bets = result;
          });
        }
        $scope.ok = function () {
          $uibModalInstance.close();
        };
      };

      // Open the modal dialog
      $uibModal.open({
        templateUrl: 'templates/otherbets.html',
        controller: otherBetsCtrl
      });
    };
  });
