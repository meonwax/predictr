'use strict';

angular.module('predictrApp')
  .factory('Account', function($resource) {
    return $resource('api/users/account', {}, {
      'get': {
        method: 'GET',
        transformResponse: function (data) {
          return angular.fromJson(data);
        }
      }
    });
  });
