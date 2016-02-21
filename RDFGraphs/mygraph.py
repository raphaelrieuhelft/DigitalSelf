import io
import os
import subprocess

import rdflib
from rdflib import RDF, RDFS, Literal
import rdflib.tools.rdf2dot
from unidecode import unidecode

schema = rdflib.namespace.Namespace('http://schema.org/')
my = rdflib.namespace.Namespace('custom/')

tmp = os.path.join(os.path.dirname(__file__), 'tmp')

common_types = [ schema.Text, schema.Date ]


class MyGraph(rdflib.Graph):
    def __init__(self, *args, **kwargs):
        rdflib.Graph.__init__(self, *args, **kwargs)
        self.bind("schema", schema)
        self.bind("my", my)

    def bnode(self, label=None):
        bn = rdflib.BNode()
        if label is not None:
            self.add((bn, RDFS.label, Literal(label)))
        return bn

    def parse_photo(self, photo):
        """
        :param photo: a FacebookData instance with data_type "PHOTO"
        :type photo: :class:`neemi.models.FacebookData`
        """
        main = self.bnode(label=photo.idr)
        self.add((main, RDF.type, my.Photograph))
        data = photo.data
        if 'backdated_time' in data:
            date = Literal(data['backdated_time'])
            self.add((date, RDF.type, schema.Date))
            self.add((main, schema.dateCreated, date))
        if 'backdated_time_granularity' in data:
            granularity = Literal(data['backdated_time_granularity'])
            self.add((granularity, RDF.type, my.Granularity))
            self.add((main, my.dateCreatedGranularity, granularity))
        if 'tags' in data:
            for tag in data['tags']['data']:
                bn = self.bnode(label=unidecode(tag['name']))
                self.add((bn, RDF.type, schema.Person))
                name=Literal(unidecode(tag['name']))
                self.add((name, RDF.type, schema.Text))
                self.add((bn, schema.name, name))
                self.add((main, schema.about, bn))
        if 'created_time' in data:
            createdTime = Literal(data['created_time'])
            self.add((createdTime, RDF.type, schema.Date))
            self.add((main, schema.datePublished, createdTime))
        if 'updated_time' in data:
            updatedTime = Literal(data['updated_time'])
            self.add((updatedTime, RDF.type, schema.Date))
            self.add((main, schema.dateModified, updatedTime))
        if 'place' in data:
            FBLocation = data['place']['location']
            if FBLocation['name'] is not None:
                placeLabel = FBLocation['name']
            else:
                placeLabel = "Photo location"
            place = self.bnode(label=placeLabel)
            self.add((place, RDF.type, schema.Place))
            self.add((main, schema.contentLocation, place))
            address_components = ["street", "zip", "city", "state", "country"]
            if len(set(FBLocation.keys()) & set(address_components)):
                address=self.bnode(label=placeLabel)
                self.add((address, RDF.type, schema.PostalAddress))
                self.add((place, schema.address, address))
                if 'street' in FBLocation:
                    streetAddress = Literal(FBLocation['street'])
                    self.add((streetAddress, RDF.type, schema.Text))
                    self.add((address, schema.streetAddress, streetAddress))
                if 'zip' in FBLocation:
                    zip = Literal(FBLocation['zip'])
                    self.add((zip, RDF.type, schema.Text))
                    self.add((address, schema.postalCode, zip))
                if 'city' in FBLocation:
                    city = Literal(FBLocation['city'])
                    self.add((city, RDF.type, schema.Text))
                    self.add((address, schema.addressLocality, city))
                if 'state' in FBLocation:
                    state = Literal(FBLocation['state'])
                    self.add((state, RDF.type, schema.Text))
                    self.add((address, schema.addressRegion, state))
                if 'country' in FBLocation:
                    country = Literal(FBLocation['country'])
                    self.add((country, RDF.type, schema.Text))
                    self.add((address, schema.addressCountry, country))
            if 'latitude' in FBLocation and 'longitude' in FBLocation:
                geo = self.bnode(label="g")
                self.add((geo, RDF.type, schema.GeoCoordinates))
                self.add((place, schema.geo, geo))
                lat = Literal(FBLocation['latitude'])
                lon = Literal(FBLocation['longitude'])
                self.add((lat, RDF.type, schema.Number))
                self.add((lon, RDF.type, schema.Number))
                self.add((geo, schema.latitude, lat))
                self.add((geo, schema.longitude, lon))
        if 'from' in data:
            name = Literal(unidecode(data['from']['name']))
            self.add((name, RDF.type, schema.Text))
            uploader = self.bnode(label=unidecode(data['from']['name']))
            self.add((main, schema.publisher, uploader))
            self.add((uploader, schema.name, name))
        #if 'event' in data:
            #parse event ?
            #event node with id ?
        if 'name' in data:
            description = Literal(unidecode(data['name']))
            self.add((description, RDF.type, schema.Text))
            self.add((main, schema.description, description))

    # def parse_photo(self, photo):
    #     main = g.bnode(label=?)
    #     g.add(main, RDF.type, my.Photograph)
    #     if ... is not None:
    #         date = Literal(...) #backdated_time
    #         g.add(date, RDF.type, schema.Date)
    #         g.add(main, schema.dateCreated, date)
    #     schema.about(schema.Person): people present and maybe more
    #     schema.datePublished(schema.Date): created_time
    #     schema.dateModified(schema.Date): updated_time
    #     schema.contentLocation(schema.Place): place
    #     schema.publisher(schema.Person): from
    #     schema.recordedAt(my.Event) with its label?
    #     schema.description(schema.Text): name(caption)
    #     my.?(?): backdated_time_granularity
    #     my.dateCreatedGranularity(my.Granularity)



    # schema.attendee(schema.Person)
    # schema.endDate(schema.Date)
    # schema.location(schema.Place)
    # schema.organizer(schema.Person)
    # schema.recordedIn(schema.CreativeWork>my.Photograph)
    # schema.startDate(schema.Date)
    # schema.description(schema.Text)
    # schema.name(schema.Text)
    # schema.duration(schema.Duration)?
    # my.startBefore(schema.Date)
    # my.endAfter(schema.Date)



    def add_person(self, name):
        namelit = rdflib.Literal(name)
        if (None, schema.name, namelit) in self:
            return self.value(predicate=schema.name, object=namelit)
        bn = self.bnode(label=name)
        self.add((bn, RDF.type, schema.Person))
        self.add((bn, schema.name, namelit))
        return bn

    # update graph representing an event using graph gph representing a photograph
    def absorb_photograph(self, gph):
        event = self.mainnode
        photo = gph.mainode
        assert (event, RDF.type, my.Event) in self
        assert (photo, RDF.type, my.Photograph) in gph
        self.add((photo, RDF.type, my.Photograph))
        self.add((event, schema.recordedIn, photo))
        # Persons
        for person in gph.objects(photo, schema.publisher):
            if (person, RDF.type, schema.Person) in gph:
                pnode = self.add_person(gph.value(subject=person, predicate=schema.name))
                self.add((event, schema.attendee, pnode))
        for person in gph.objects(photo, schema.about):
            if (person, RDF.type, schema.Person) in gph:
                pnode = self.add_person(gph.value(subject=person, predicate=schema.name))
                self.add((event, schema.attendee, pnode))
        # TODO


# We suppose that the publisher was at the event


    # schema.attendee(schema.Person)
    # schema.endDate(schema.Date)
    # schema.location(schema.Place)
    # schema.organizer(schema.Person)
    # schema.recordedIn(schema.CreativeWork>my.Photograph)
    # schema.startDate(schema.Date)
    # schema.description(schema.Text)
    # schema.name(schema.Text)
    # schema.duration(schema.Duration)?
    # my.startBefore(schema.Date)
    # my.endAfter(schema.Date)


    def elaborate_my_types(self):
        if (None, None, my.Event) in self:
            self.add(my.Event, RDFS.subClassOf, schema.Event)
        if (None, None, my.Photograph) in self:
            self.add(my.Photograph, RDFS.subClassOf, schema.Photograph)


    def draw(self, name='default', lighten_types=False):
        if lighten_types:
            g = MyGraph()
            g += self
            for t in common_types:
                g.remove((None, RDF.type, t))
            g.draw(name=name)
            return
        path_dot = os.path.join(tmp, name+'_dot')
        with io.open(path_dot, mode='w', newline='') as f:
            rdflib.tools.rdf2dot.rdf2dot(self, f)
        path_png = os.path.join(tmp, name+'.png')
        subprocess.call(["dot", "-Tpng", path_dot, "-o", path_png], shell=True)


if __name__ == '__main__':
    g = MyGraph()
    g.parse(tmp+'/project_statement_example.n3', format='n3')
    #print(g.serialize(format='n3'))
    g.draw('project_statement_example')

