'use strict';

angular.module('predictrApp')
  .factory('ServerInfo', function($resource, $timeout) {
    return {
      get: function() {
        return $resource('api/info', {}, {
          'get': {
            method: 'GET',
            transformResponse: function (data) {
              return angular.fromJson(data);
            }
          }
        });
      },
      /*
       * AngularJS Server Time Sync
       * https://github.com/idangozlan/angular-server-time
       * Built by Idan Gozlan (c)
       */
      serverClock: function() {
        var obj = {};
        obj.timeOffset = 0;
        obj.init = function(serverTime) {
          obj.timeOffset = serverTime * 1000 - new Date().getTime();
          obj.updateClock();
          return obj;
        };
        obj.updateClock = function() {
          obj.time = (new Date(new Date().getTime() + obj.timeOffset).getTime()) / 1000;
          $timeout(obj.updateClock, 1000);
        };
        return obj;
      }
    };
  });
