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

    $scope.updatePassword = function() {
      $scope.updatingPassword = true;

      var passwordData = {
        'oldPassword': $scope.password.old,
        'newPassword': $scope.password.new
      };

      User.password().save(passwordData,
        function() {
          $scope.updatingPassword = false;
          $scope.password = null;
          $scope.passwordError = false;
          toastr.success($translate.instant('settings.passwordOk'));
        },
        function() {
          $scope.updatingPassword = false;
          // Clear input fields to avoid typos
          $scope.password = null;
          $scope.passwordError = true;
        }
      );
    };
  });
