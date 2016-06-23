'use strict';

  angular.module('predictrApp')
  .controller('SettingsCtrl', function($rootScope, $scope, $timeout, $translate, amMoment, toastr, User) {

    $timeout(function () {
      $scope.language = $rootScope.account.preferredLanguage || $translate.use();
      $scope.name = $rootScope.account.name;
      $scope.avatarUrl = $rootScope.account.id + '?' + new Date().getTime();
    });

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

    $scope.uploadAvatar = function() {
      $scope.uploadingAvatar = true;

      var file = document.getElementById('file').files[0], reader = new FileReader();
      reader.onloadend = function(event) {
        var binaryData = new Uint8Array(event.target.result);
        User.avatar(file.type).save(binaryData,
          function() {
            $scope.uploadingAvatar = false;
            $scope.avatarError = false;
            toastr.success($translate.instant('settings.avatarOk'));

            // Reload preview
            $scope.avatarUrl = $rootScope.account.id + '?' + new Date().getTime();
          },
          function() {
            $scope.uploadingAvatar = false;
            $scope.avatarError = true;
          }
        );
      }
      reader.readAsArrayBuffer(file);
    };

    $scope.deleteAvatar = function() {
      User.avatar().delete(
        function() {
          toastr.success($translate.instant('settings.deleteAvatarOk'));

          // Reload preview
          $scope.avatarUrl = $rootScope.account.id + '?' + new Date().getTime();
        },
        function() {
          toastr.error($translate.instant('settings.deleteAvatarError'));
        }
      );
    };

    $scope.updatePassword = function() {
      $scope.updatingPassword = true;

      var passwordData = {
        'oldPassword': $scope.password.old,
        'newPassword': $scope.password.new
      };

      User.changePassword().save(passwordData,
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
