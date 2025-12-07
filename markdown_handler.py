class MarkdownHandler:
    """
    Renders a stylish HTML card for a film entry.
    """

    @staticmethod
    def render_programme_details(movie: dict) -> str:
        """
        Returns an HTML block for a film card.
        """
        return f"""
        <div style="
            background-color:#111;
            padding:10px;
            border-radius:14px;
            margin-bottom:25px;
            border:1px solid rgba(255,255,255,0.08);
            box-shadow:0 4px 12px rgba(0,0,0,0.2);
            max-width: 650px;
        ">

            <a href="{movie.get('LETTERBOXD_URL','')}" target="_blank">
                <img src="{movie['IMAGE_URL']}" style="
                    width:100%;
                    border-radius:12px;
                    margin-bottom:15px;
                ">
            </a>

            <h2 style="margin:0; padding:0; font-size:24px; font-weight:700; color:white;">
                {movie['INTERNATIONAL_TITLE']}
            </h2>

            <p style="margin:4px 0 0 0; font-size:16px; color:#ccc;">
                {movie['ORIGINAL_TITLE']}
            </p>

            <p style="margin:12px 0; font-size:15px; color:#aaa;">
                {movie['DIRECTOR']}
            </p>

            <p style="margin:0; font-size:15px; color:#bbb;">
                {movie['YEAR']} | {int(movie['RUNNING_TIME'])//60} Hr {int(movie['RUNNING_TIME'])%60} Min
            </p>

            <p style="margin:0 0 16px 0; font-size:15px; color:#bbb;">
                {movie['LANGUAGE']} | {movie['COUNTRY']}
            </p>

            <details>
            <summary><b>Synopsis</b></summary>
            <p>{movie['SYNOPSIS']}</p>
            </details>

        </div>
        """

    @staticmethod
    def render_programme_image(movie: dict) -> str:
        """
        Returns an HTML block for a film card.
        """
        return f"""
        <div style="
            background-color:#111;
            padding:10px;
            border-radius:14px;
            margin-bottom:25px;
            border:1px solid rgba(255,255,255,0.08);
            box-shadow:0 4px 12px rgba(0,0,0,0.2);
            max-width: 650px;
        ">

            <a href="{movie.get('LETTERBOXD_URL','')}" target="_blank">
                <img src="{movie['IMAGE_URL']}" style="
                    width:100%;
                    border-radius:12px;
                    margin-bottom:15px;
                ">
            </a>

        </div>
        """
