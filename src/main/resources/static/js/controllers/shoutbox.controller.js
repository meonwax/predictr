'use strict';

angular.module('predictrApp')
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
  });
