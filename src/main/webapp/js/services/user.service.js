'use strict';

angular.module('predictrApp')
  .factory('User', function($q, $http, $resource) {
    return {
      account: function() {
        return $resource('api/users/account');
      },
      register: function() {
        return $resource('api/users/register');
      },
      password: function() {
        return $resource('api/users/password');
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
