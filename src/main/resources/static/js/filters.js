'use strict';

angular.module('predictrApp')
  .filter('myDate', function($filter, $translate) {
    return function(timestamp) {
      let dateString = $filter('amDateFormat')(timestamp * 1000, 'lll z');
      return timezoneTranslator($translate, dateString);
    };
  })
  .filter('myDateShort', function($filter) {
    return function(timestamp) {
      return $filter('amDateFormat')(timestamp * 1000, 'L LT');
    };
  })
  .filter('myDateLong', function($filter, $translate) {
    return function(timestamp) {
      let dateString = $filter('amDateFormat')(timestamp * 1000, 'll LTS z');
      return timezoneTranslator($translate, dateString);
    };
  })
  .filter('playTime', function() {
    return function(timestamp) {
      let diffSeconds = Date.now() / 1000 - timestamp;
      let diffMinutes = Math.floor(diffSeconds / 60);
      let diffHours = Math.floor(diffMinutes / 60);
      return diffHours + ':' + ('0' + (diffMinutes - diffHours * 60)).slice(-2) + 'h';
    };
  })
  .filter('bet', function($filter) {
    return function(bet) {
      return bet ? bet.scoreHome + ':' + bet.scoreAway : null;
    };
  })
  .filter('rank', function($filter) {
    return function(rank) {
      return rank ? rank + '.' : '';
    };
  });

let timezoneTranslator = function($translate, dateString) {
  switch($translate.use()) {
    case 'de':
      return dateString.replace(new RegExp("CEST", 'g'), "MESZ");
    default:
      return dateString;
  }
};
