'use strict';

angular.module('predictrApp')
  .controller('AdminCtrl', function($rootScope, $scope, users) {

    $rootScope.loading = false;
    $scope.users = users;
  });
