package com.example;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * This class is generated by the JSON to Java Class Generator.
 */
public class Address {
    @JsonProperty(access = JsonProperty.Access.AUTO, value = "city")
    private String city;

    @JsonProperty(access = JsonProperty.Access.AUTO, value = "street")
    private String street;

    @JsonProperty(access = JsonProperty.Access.AUTO, value = "zip")
    private String zip;

    public String getCity() {
        return city;
    }

    public void setCity(String city) {
        this.city = city;
    }

    public String getStreet() {
        return street;
    }

    public void setStreet(String street) {
        this.street = street;
    }

    public String getZip() {
        return zip;
    }

    public void setZip(String zip) {
        this.zip = zip;
    }

}
