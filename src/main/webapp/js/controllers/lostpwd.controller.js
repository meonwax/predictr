'use strict';

angular.module('predictrApp')
  .controller('LostPasswordCtrl', function($scope, $location, $translate, toastr, User) {

    $scope.focusInput = true;

    $scope.request = function() {
      $scope.focusInput = false;
      $scope.loading = true;

      User.resetPassword().save($scope.email,
        function() {
          $scope.error = false;
          $scope.loading = false;
          toastr.success($translate.instant('lostpwd.ok'), {timeOut: 5000});
          $location.path('login');
        },
        function() {
          $scope.loading = false;
          $scope.focusInput = true;
          $scope.error = true;
        }
      );
    };
  });
