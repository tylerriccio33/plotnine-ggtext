import pandas as pd
from plotnine import aes, geom_point, ggplot, labs, theme_minimal, xlim, ylim
from plotnine.data import mtcars

from plotnine_ggtext import geom_richtext, geom_textbox, unit

cars = mtcars.query("name in ['Toyota Corolla', 'Maserati Bora', 'Cadillac Fleetwood']")
cars = cars.assign(label=lambda d: "**" + d["name"] + "**<br>" + d["mpg"].astype(str) + " *mpg*")

note = pd.DataFrame({"wt": [4.0], "mpg": [31.0], "label": [
    "Heavier cars burn **more fuel**. The *Corolla* gets "
    "<span style='color:#D1495B'>over 33 mpg</span>, "
    "while the *Fleetwood* manages just 10.4."
]})

p = (
    ggplot(mtcars, aes("wt", "mpg"))
    + geom_point(color="#8D99AE", size=3)
    + geom_richtext(aes(label="label"), data=cars, fill="#FFF8E7",
                    label_color="#EDAE49", hjust="inward", vjust=0, nudge_y=0.6)
    + geom_textbox(aes(label="label"), data=note, width=unit(2.4, "in"),
                   fill="#EEF4FB", box_color="none", size=12)
    + ylim(9, 39)
    + labs(x="Weight (1000 lbs)", y="Miles per gallon")
    + theme_minimal()
)
p.save("demo.png", width=8, height=5, dpi=110, verbose=False)
print("saved demo.png")
