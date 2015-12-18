'use strict';

angular.module('predictrApp')
  .factory('ServerInfo', function($resource) {
    return $resource('api/info', {}, {
      'get': {
        method: 'GET',
        transformResponse: function (data) {
          return angular.fromJson(data);
        }
      }
    });
  });
