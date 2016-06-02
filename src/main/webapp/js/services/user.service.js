'use strict';

angular.module('predictrApp')
  .factory('User', function($q, $http, $resource) {
    return {
      account: function() {
        return $resource('api/users/account');
      },
      register: function(credentials) {
        var deferred = $q.defer();
        $http.post('api/users/register', credentials).then(function() {
          deferred.resolve();
        }, function(error) {
          deferred.reject(error);
        });
        return deferred.promise;
      },
      all: function() {
        return $resource('api/users', {}, {
          'query': {
            method: 'GET',
            isArray: true
          }
        });
      },
    };
  });
