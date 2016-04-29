'use strict';

angular.module('predictrApp')
  .config(function($routeProvider) {
    $routeProvider.when('/admin', {
      templateUrl: 'templates/admin.html',
      controller: 'AdminCtrl',
      activeTab: 'admin',
      resolve: {
        users: function($rootScope, $q, User) {
          $rootScope.loading = true;
          var deferred = $q.defer();
          User.all().get(function(users) {
            deferred.resolve(users);
          });
          return deferred.promise;
        }
      }
    });
  });
