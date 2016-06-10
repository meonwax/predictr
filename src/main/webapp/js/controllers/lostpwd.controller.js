'use strict';

angular.module('predictrApp')
  .controller('LostPasswordCtrl', function($scope, $location, $translate, toastr, User) {

    $scope.focusInput = true;

    $scope.request = function() {
      $scope.focusInput = false;
      $scope.sending = true;

      User.resetPassword().save($scope.email,
        function() {
          $scope.error = false;
          $scope.sending = false;
          toastr.success($translate.instant('lostpwd.ok'), {timeOut: 5000});
          $location.path('login');
        },
        function() {
          $scope.sending = false;
          $scope.focusInput = true;
          $scope.error = true;
        }
      );
    };
  });
