import re

class Metar:

    _REPORT_TYPE = 'report_type'
    _STATION = 'station'
    _DATE_TIME = 'date_time'
    _REPORT_MODIFIER = 'report_modifier'
    _WIND = 'wind'
    _WIND_SPEED = 'wind_speed'
    _WIND_DIRECTION = 'wind_direction'
    _WIND_GUST = 'wind_gust'
    _VARIABLE_WIND_DIRECTION = 'variable_wind_direction'
    _VISIBILITY = 'visibility'

    _matches = {}

    #pylint: disable=anomalous-backslash-in-string
    _body_fields = {
        _REPORT_TYPE: '^(METAR|SPECI)$',
        _STATION:  '^[A-Z]{4}$',
        _DATE_TIME: '^\d{6}Z$',
        _REPORT_MODIFIER: '^(AUTO|COR)$',
        _WIND: '^(?P<w_dir>(\d{3}|VRB))(?P<w_speed>\d{2,3})(?P<w_gust>G\d{2,3})?KT',
        _VARIABLE_WIND_DIRECTION: '^(?P<vrb_from>\d{3})V(?P<vrb_to>\d{3})',
        _VISIBILITY: '^(\d{1}\s)?\d?(\/)?\dSM$'
    }

    _remarks_fields = {}

    def __init__(self, raw_metar):
        self.raw = raw_metar
        self._parse(raw_metar)


    def __repr__(self):
        return str(self._matches)

t
    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            # Not yet parsed out - fall through to the processing options below
            pass

        if name.startswith('raw_'):
            return self._raw_handler(name)

        if name in (self._WIND_DIRECTION, self._WIND_SPEED, self._WIND_GUST, self._VARIABLE_WIND_DIRECTION):
            return self._wind_handler(name)

        if name == 'datetime':
            return self._datetime_handler()


    def _tokenize(self, raw_metar):
        """ Generally, tokenizing simply involves splitting at all whitespace.
        However visibility can contain a single space within its value
        (ex: 1 1/2SM) so we need to extract that first. The wind condition also
        may contain a space in the event of a variable wind direction with a
        speed > 6kts; however we're treating that as a separate field. """
        split_vis = '\s\d{1}\s\d{1,2}\/\d{1,2}SM\s'
        match = re.search(split_vis, raw_metar)
        if match:
            tokens = raw_metar[:match.start()].split(' ')
            tokens.append((raw_metar[match.start():match.end()]).strip())
            tokens += raw_metar[match.end():].split(' ')
        else:
            tokens = raw_metar.split(' ')
        return tokens


    def _parse_token(self, token, fields):
        for field, regex in fields.items():
            m = regex.match(token)
            if m:
                self._matches[field] = m
                fields.pop(field)
                break
        return fields


    def _parse(self, raw_metar):
        tokens = self._tokenize(raw_metar)
        fields = {k: re.compile(v) for k, v in self._body_fields.items()}
        for token in tokens:
            if token == 'RMK':
                fields = {k: re.compile(v) for k, v in self._remarks_fields.items()}
            else:
                fields = self._parse_token(token, fields)


    def _raw_handler(self, name):
        self.__dict__[name] = self._matches.get(name[len('raw_'):]).group()
        return self.__dict__[name]


    def _wind_handler(self, name):
        if name == self._VARIABLE_WIND_DIRECTION:
            try:
                match = self._matches[self._VARIABLE_WIND_DIRECTION]
                self.__dict__[name] = {'from': int(match.group('vrb_from')),
                                       'to': int(match.group('vrb_to'))}
            except KeyError:
                self.__dict__[name] = None
        else:
            match = self._matches[self._WIND]
            if match:
                self.__dict__[self._WIND_SPEED] = int(match.group('w_speed'))
                self.__dict__[self._WIND_DIRECTION] = int(match.group('w_dir'))
                gust = match.group('w_gust')
                self.__dict__[self._WIND_GUST] = int(gust[1:]) if gust else None
            else:
                self.__dict__[self._WIND_SPEED] = None
                self.__dict__[self._WIND_DIRECTION] = None
                self.__dict__[self._WIND_GUST] = None
            return self.__dict__[name]


    def _datetime_handler(self):
        try:
            return datetime.strptime(self._matches[self._DATE_TIME], '%d%H%M')
        except KeyError:
            return None


def test():
#    m1 = 'KATL 150006Z 29017G28KT 10SM FEW036 SCT046 BKN140 BKN200 19/13 A2965 RMK AO2 PK WND 29029/2354 WSHFT 2339 CB DSNT SE T01940128 $'
    m1 = 'KATL 150006Z 29017G28KT 1 1/2SM FEW036 SCT046 BKN140 BKN200 19/13 A2965 RMK AO2 PK WND 29029/2354 WSHFT 2339 CB DSNT SE T01940128 $'
#    m1 = 'KATL 150006Z 29017G28KT 1 1/2SM FEW036 SCT046 BKN140 BKN200 19/13 A2965 RMK AO2 PK WND 29029/2354 WSHFT 2339 CB DSNT SE T01940128 $'
    metar1 = Metar(m1)
    print(metar1)
    print(metar1.wind_direction)
    print(metar1.wind_speed)
    print(metar1.wind_gust)

test()
