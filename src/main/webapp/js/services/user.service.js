'use strict';

angular.module('predictrApp')
  .factory('User', function($q, $http) {
    return {
      // account: function() {
      //   return $resource('api/users/account', {}, {
      //     'get': {
      //       method: 'GET',
      //       transformResponse: function (data) {
      //         return angular.fromJson(data);
      //       }
      //     }
      //   });
      // },
      register: function(credentials) {
        var deferred = $q.defer();
        $http.post('api/users/register', credentials).then(function() {
          deferred.resolve();
        }, function(error) {
          deferred.reject(error);
        });
        return deferred.promise;
      }
    }
  });
