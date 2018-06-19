'use strict';

angular.module('predictrApp')
  .factory('Authentication', function($rootScope, $q, $http, $window) {
    return {
      login: function(credentials) {
        var deferred = $q.defer();
        var data = 'email=' + encodeURIComponent(credentials.email) + '&password=' + encodeURIComponent(credentials.password);
        if(credentials.rememberMe) {
          data += '&remember-me=1';
        }
        $http.post('api/users/login', data, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8; charset=utf-8'
          }
        }).then(function() {
          deferred.resolve();
        }, function(error) {
          deferred.reject(error);
        });
        return deferred.promise;
      },

      logout: function() {
        var deferred = $q.defer();
        $http.get('api/users/logout').then(function() {
          deferred.resolve();
        }, function(error) {
          deferred.reject(error);
        });
        return deferred.promise;
      },

      isPageEnabled: function(page) {
        if($rootScope.serverInfo && $rootScope.serverInfo.pagesBlacklist) {
          return $rootScope.serverInfo.pagesBlacklist.indexOf(page) == -1;
        }
        return true;
      }
    };
  });
