'use strict';

angular.module('predictrApp')
  .controller('SettingsCtrl', function($rootScope, $scope, $translate, toastr, User) {
    $scope.language = $rootScope.account.preferredLanguage || $translate.use();
    $scope.name = $rootScope.account.name;

    $scope.edit = function() {
      $scope.editing = true;

      var userData = {
        'name': $scope.name,
        'preferredLanguage': $scope.language
      };

      User.account().save(userData,
        function(result) {
          // Immediately use the new preferred language
          $translate.use(result.preferredLanguage);
          toastr.success($translate.instant('settings.editOk'));

          $scope.editing = false;
          $scope.editError = false;

          // Update existing account in webapp
          $rootScope.account = result;
        },
        function() {
          $scope.editing = false;
          $scope.editError = true;
        }
      );
    };
  });
