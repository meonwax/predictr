'use strict';

angular.module('predictrApp')
  .controller('AdminCtrl', function($rootScope, $scope, toastr, $translate, Game, games, users) {
    $rootScope.loading = false;
    $scope.games = games;
    $scope.users = users;

    $scope.send = function() {
      $scope.saving = true;

      // Prepare DTO array to save
      var dtos = [];
      angular.forEach($scope.games, function(game) {
        if(game.scoreHome && game.scoreAway) {
          dtos.push({
            'scoreHome': game.scoreHome,
            'scoreAway': game.scoreAway,
            'id': game.id
          });
        }
      });

      // Actually save it
      Game.all().save(dtos,
        function() {
          toastr.success($translate.instant('admin.saveOk'));
          $scope.saving = false;
        },
        function(response) {
          var errorMessage = $translate.instant('admin.saveError') + '<br>' + response.status + ': ' + response.statusText;
          toastr.error(errorMessage);
          $scope.saving = false;
        }
      );
    };
  });
