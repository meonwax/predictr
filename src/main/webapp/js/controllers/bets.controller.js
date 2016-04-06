'use strict';

angular.module('predictrApp')
  .controller('BetsCtrl', function($scope, $location, $anchorScroll, $timeout, $translate, toastr, Group, Bet) {
    var query = function() {
      $scope.loading = false;
      $scope.groups = Group.query();
    };
    $scope.send = function() {
      $scope.loading = true;
      Bet.save({},
        function() {
          toastr.success($translate.instant('bets.saveOk'));
          query();
        },
        function(response) {
          var errorMessage = $translate.instant('bets.saveError') + '<br>' + response.status + ': ' + response.statusText;
          toastr.error(errorMessage);
          $scope.loading = false;
          //query();
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
