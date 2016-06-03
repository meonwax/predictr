'use strict';

angular.module('predictrApp')
  .controller('SettingsCtrl', function($rootScope, $scope, $translate, amMoment, toastr, User) {
    $scope.language = $rootScope.account.preferredLanguage || $translate.use();
    $scope.name = $rootScope.account.name;

    $scope.edit = function() {
      $scope.editing = true;

      var userData = {
        'name': $scope.name,
        'preferredLanguage': $scope.language
      };

      User.account().save(userData,
        function(user) {
          // Immediately use the new preferred language
          $translate.use(user.preferredLanguage);
          amMoment.changeLocale(user.preferredLanguage);
          toastr.success($translate.instant('settings.editOk'));

          $scope.editing = false;
          $scope.editError = false;

          // Update existing account in webapp
          $rootScope.account = user;
        },
        function() {
          $scope.editing = false;
          $scope.editError = true;
        }
      );
    };
  });
