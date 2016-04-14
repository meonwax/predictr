'use strict';

angular.module('predictrApp')
  .factory('Authentication', function($q, $http, localStorageService) {

    // Initialize token
    var token = localStorageService.get('authenticationToken');

    return {
      login: function(credentials) {
        var deferred = $q.defer();
        var data = 'email=' + encodeURIComponent(credentials.email) + '&password=' + encodeURIComponent(credentials.password);
        $http.post('api/users/login', data, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8; charset=utf-8'
          }
        }).then(function() {
          token = btoa(credentials.email + Date.now().toString());
          localStorageService.set('authenticationToken', token);
          deferred.resolve();
        }, function(error) {
          deferred.reject(error);
        });
        return deferred.promise;
      },

      logout: function() {
        var deferred = $q.defer();
        $http.get('api/users/logout').then(function() {
          localStorageService.clearAll();
          token = null;
          deferred.resolve();
        }, function(error) {
          deferred.reject(error);
        });
        return deferred.promise;
      },

      getToken: function() {
        return token;
      }
    }
  });
