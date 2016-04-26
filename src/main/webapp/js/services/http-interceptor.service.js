'use strict';

angular.module('predictrApp')
  .factory('HttpInterceptorService', function($rootScope) {
    return {
      responseError: function(response) {
        if (response.status == 401) {
          $rootScope.logout();
        }
        // TODO: Handle AJAX errors here
        return response;
      }
    };
  });
