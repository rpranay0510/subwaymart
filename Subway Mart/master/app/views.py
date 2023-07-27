from app import app, models
from app.forms import AddForm, EditForm, ProductMovementForm
from flask import abort, flash, redirect, request, render_template, url_for
import sqlalchemy as sa


@app.route("/")
def home():
    page_title = "Home"
    return render_template("home.html", page_title=page_title)


@app.route("/products")
def products():
    prods = models.Product.query.all()
    page_title = "Products"
    return render_template("products.html", page_title=page_title, products=prods)


@app.route("/products/add", methods=["GET", "POST"])
def add_product():
   
    form = AddForm()
    if request.method == "POST" and form.validate_on_submit():
        product = models.Product(name=form.name.data, description=form.description.data)
        
        try:
            models.db.session.add(product)
            models.db.session.commit()
            flash("Product added successfully", "success")
            return redirect(url_for("products"))
        except sa.exc.IntegrityError:
            flash("Product name exists", "danger")
    page_title = "Add Product"
    form_type = "Product"
    return render_template("add.html", page_title=page_title, form=form, form_type=form_type)


@app.route("/products/<name>/edit", methods=["GET", "POST"])
def edit_product(name):
    product = models.Product.query.filter(sa.func.lower(models.Product.name) == sa.func.lower(name)).first()
    if product:
        form = EditForm(obj=product)
        if request.method == "POST" and form.validate_on_submit():
            product.name = form.name.data
            product.description = form.description.data 
            try:
                models.db.session.commit()
                flash("Product edited successfully", "success")
                return redirect(url_for("products"))
            except sa.exc.IntegrityError:
                flash("Product name exists", "danger") 
        page_title = "Edit Product"
        form_type = "Product"
        return render_template("edit.html", page_title=page_title, form=form, form_type=form_type)
    else:
        abort(404)


@app.route('/products/<name>')
def view_product(name):

    product = models.Product.query.filter(sa.func.lower(models.Product.name) == sa.func.lower(name)).first()
    if product:
        page_title = "{}".format(product.name)
        return render_template("view.html", page_title=page_title, product=product)
    else:
        abort(404)


@app.route("/locations")
def locations():
    locs = models.Location.query.all() 
    page_title = "Locations"
    return render_template("locations.html", page_title=page_title, locations=locs)


@app.route("/locations/add", methods=["GET", "POST"])
def add_location():
   
    form = AddForm()
    if request.method == "POST" and form.validate_on_submit():
        location = models.Location(name=form.name.data, description=form.description.data)
        
        try:
            models.db.session.add(location)
            models.db.session.commit()
            flash("Location added successfully", "success")
            return redirect(url_for("locations"))
        except sa.exc.IntegrityError:
            flash("Location name exists", "danger")
    page_title = "Add Location"
    form_type = "Location"
    return render_template("add.html", page_title=page_title, form=form, form_type=form_type)


@app.route("/locations/<name>/edit", methods=["GET", "POST"])
def edit_location(name): 

    location = models.Location.query.filter(sa.func.lower(models.Location.name) == sa.func.lower(name)).first()
    if location:
        form = AddForm(obj=location)
        if request.method == "POST" and form.validate_on_submit():
            location.name = form.name.data
            location.description = form.description.data
            
            try:
                models.db.session.commit()
                flash("Location edited successfully", "success")
                return redirect(url_for("locations"))
            except sa.exc.IntegrityError:
                flash("Location name exists", "danger")
        page_title = "Edit Location"
        form_type = "Location"
        return render_template("edit.html", page_title=page_title, form=form, form_type=form_type)
    else:
        abort(404)


@app.route('/locations/<name>')
def view_location(name):

    location = models.Location.query.filter(sa.func.lower(models.Location.name) == sa.func.lower(name)).first()
    
    if location:
        
        results = models.Product.query.all()
        products = []
        quantity = []
        for product in results:
            incoming = models.db.session.query(sa.func.sum(models.ProductMovement.qty)).filter(
                models.ProductMovement.to_location == location.id).filter(
                models.ProductMovement.product_id == product.id).scalar()
            outgoing = models.db.session.query(sa.func.sum(models.ProductMovement.qty)).filter(
                models.ProductMovement.from_location == location.id).filter(
                models.ProductMovement.product_id == product.id).scalar()
            if incoming is None:
                incoming = 0
            if outgoing is None:
                outgoing = 0
            
            if incoming > 0:
                products.append(product)
                quantity.append(incoming - outgoing)
        page_title = "{}".format(location.name)
        return render_template("view.html", page_title=page_title, products=products, location=location, quantity=quantity)
    else:
        abort(404)


@app.route("/movements")
def movements():
    movs = models.ProductMovement.query.all()
    page_title = "Movements"
    return render_template("movements.html", page_title=page_title, movements=movs)


@app.route("/movements/add", methods=["GET", "POST"])
def add_movement():
    
    form = ProductMovementForm() 
    form.product.choices = [(product.id, product.name) for product in models.Product.query.all()]
    form.from_location.choices = [(location.id, location.name) for location in models.Location.query.all()]
    form.to_location.choices = [(location.id, location.name) for location in models.Location.query.all()]
    if request.method == "POST" and form.validate_on_submit():
        abroad = 1
        
        if form.from_location.data == form.to_location.data:
            flash("Failed attempt to move product to the same location", "danger") 
        elif form.from_location.data != abroad:
            incoming = models.db.session.query(sa.func.sum(models.ProductMovement.qty)).filter(
                models.ProductMovement.to_location == form.from_location.data).filter(
                models.ProductMovement.product_id == form.product.data).scalar()
            outgoing = models.db.session.query(sa.func.sum(models.ProductMovement.qty)).filter(
                models.ProductMovement.from_location == form.from_location.data).filter(
                models.ProductMovement.product_id == form.product.data).scalar()
            if incoming is None:
                incoming = 0
            if outgoing is None:
                outgoing = 0

            if outgoing + form.qty.data <= incoming:
                movement = models.ProductMovement(from_location=form.from_location.data, to_location=form.to_location.data,
                                                  description=form.description.data,
                                                  product_id=form.product.data, qty=form.qty.data)
                models.db.session.add(movement)
                models.db.session.commit()
                flash("Product moved successfully", "success")
                return redirect(url_for("movements"))
            elif incoming == 0:
                flash("Product doesn't exist in this location", "danger")
            else:
                remnant = incoming - outgoing
                flash("Only a maximum of {} can be moved from this location".format(remnant),
                      "danger")
        
        else:
            movement = models.ProductMovement(from_location=form.from_location.data, to_location=form.to_location.data,
                                              description=form.description.data,
                                              product_id=form.product.data, qty=form.qty.data)
            models.db.session.add(movement)
            models.db.session.commit()
            flash("Product moved successfully", "success")
            return redirect(url_for("movements"))
    page_title = "Add Movement"
    form_type = "Movement"
    return render_template("add.html", page_title=page_title, form=form, form_type=form_type)


@app.route("/movements/<int:number>/edit", methods=["GET", "POST"])
def edit_movement(number):
   
    movement = models.ProductMovement.query.filter(models.ProductMovement.id == number).first()
    if movement:
        form = ProductMovementForm(obj=movement)
       
        form.product.choices = [(product.id, product.name) for product in models.Product.query.all()]
        form.from_location.choices = [(location.id, location.name) for location in models.Location.query.all()]
        form.to_location.choices = [(location.id, location.name) for location in models.Location.query.all()]
        if request.method == "POST" and form.validate_on_submit():
            abroad = 1
           
            if form.from_location.data == form.to_location.data:
                flash("Failed attempt to move product to the same location", "danger")
            
            elif form.from_location.data != abroad:
                incoming = models.db.session.query(sa.func.sum(models.ProductMovement.qty)).filter(
                    models.ProductMovement.to_location == form.from_location.data).filter(
                    models.ProductMovement.product_id == form.product.data).scalar()
                outgoing = models.db.session.query(sa.func.sum(models.ProductMovement.qty)).filter(
                    models.ProductMovement.from_location == form.from_location.data).filter(
                    models.ProductMovement.product_id == form.product.data).scalar()
                if incoming is None:
                    incoming = 0
                if outgoing is None:
                    outgoing = 0
                if outgoing + form.qty.data <= incoming:
                    movement = models.ProductMovement(from_location=form.from_location.data, to_location=form.to_location.data,
                                                      description=form.description.data,
                                                      product_id=form.product.data, qty=form.qty.data)
                    models.db.session.add(movement)
                    models.db.session.commit()
                    flash("Movement edited successfully", "success")
                    return redirect(url_for("movements"))
                elif incoming == 0:
                    flash("Product doesn't exist in this location", "danger")
                else:
                    remnant = incoming - outgoing
                    flash("Only a maximum of {} can be moved from this location".format(remnant),
                          "danger")
            
            else:
                movement = models.ProductMovement(from_location=form.from_location.data,
                                                  to_location=form.to_location.data,
                                                  description=form.description.data,
                                                  product_id=form.product.data, qty=form.qty.data)
                models.db.session.add(movement)
                models.db.session.commit()
                flash("Movement edited successfully", "success")
                return redirect(url_for("movements"))
        page_title = "Edit Movement"
        form_type = "Movement"
        return render_template("edit.html", page_title=page_title, form=form, form_type=form_type)
    else:
        abort(404)


@app.route("/movements/<int:number>/view")
def view_movement(number):
    
    movement = models.ProductMovement.query.filter(models.ProductMovement.id == number).first()
    if movement:
        page_title = "Movement {}".format(movement.id)
        from_location = models.Location.query.filter(models.Location.id == movement.from_location).first()
        to_location = models.Location.query.filter(models.Location.id == movement.to_location).first()
        return render_template("view.html", page_title=page_title, movement=movement, from_location=from_location,
                               to_location=to_location)
    else:
        abort(404)

@app.errorhandler(404)
def page_not_found(e):
    page_title = "Page Not Found"
    return render_template("404.html", page_title=page_title), 404
